"""
FastAPI application for InvoiceAI.
Provides API endpoints for invoice extraction using OCR and Cerebras AI.
"""

import os
import uuid
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from config import settings
from models import APIResponse, InvoiceData
from ocr import OCRProcessor
from ai_client import CerebrasClient


# Initialize FastAPI app
app = FastAPI(
    title="InvoiceAI API",
    description="AI-powered invoice data extraction using Cerebras and OCR",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
ocr_processor = None
ai_client = None

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize processors on startup."""
    global ocr_processor, ai_client
    ocr_processor = OCRProcessor()
    ai_client = CerebrasClient()
    yield
    # Cleanup on shutdown if needed

# Reinitialize app with lifespan
app = FastAPI(
    title="InvoiceAI API",
    description="AI-powered invoice data extraction using Cerebras and OCR",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    is_valid, error_msg = settings.validate()
    
    return {
        "status": "healthy" if is_valid else "degraded",
        "api_configured": is_valid,
        "error": error_msg if not is_valid else None
    }


@app.post("/api/invoice/extract", response_model=APIResponse)
async def extract_invoice(file: UploadFile = File(...)):
    """
    Extract invoice data from uploaded file.
    
    Args:
        file: Uploaded invoice file (PDF, JPG, PNG)
        
    Returns:
        APIResponse with extracted invoice data or error message
    """
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Validate Cerebras API key
        is_valid, error_msg = settings.validate()
        if not is_valid:
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = settings.UPLOAD_DIR / unique_filename
        
        try:
            # Save uploaded file
            with open(file_path, "wb") as f:
                content = await file.read()
                
                # Check file size
                if len(content) > settings.MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
                    )
                
                f.write(content)
            
            # Step 1: Extract text using OCR
            print(f"Processing file: {file.filename}")
            ocr_text = ocr_processor.process_file(str(file_path))
            
            if not ocr_text or len(ocr_text.strip()) < 10:
                raise Exception("OCR failed to extract meaningful text from the file")
            
            print(f"OCR extracted {len(ocr_text)} characters")
            
            # Step 2: Send to Cerebras for analysis
            print("Sending to Cerebras AI for analysis...")
            invoice_data = await ai_client.extract_invoice_data(ocr_text)
            
            print("Invoice data extracted successfully")
            
            # Return success response
            return APIResponse(
                success=True,
                data=invoice_data,
                ocr_text=ocr_text[:500] + "..." if len(ocr_text) > 500 else ocr_text  # Truncate for response
            )
        
        finally:
            # Clean up uploaded file
            if file_path.exists():
                file_path.unlink()
    
    except HTTPException:
        raise
    
    except Exception as e:
        error_message = str(e)
        print(f"Error processing invoice: {error_message}")
        
        return APIResponse(
            success=False,
            error=error_message
        )

# Serve frontend - MUST be after all API routes
from fastapi.responses import FileResponse

frontend_path = Path(__file__).parent.parent / "frontend"

# Serve static files
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

# Serve index.html at root
@app.get("/")
async def serve_frontend():
    """Serve the frontend index.html"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Frontend not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
