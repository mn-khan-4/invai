"""
Configuration module for InvoiceAI backend.
Loads environment variables and provides application settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    # Cerebras API Configuration
    CEREBRAS_API_KEY: str = os.getenv("CEREBRAS_API_KEY", "")
    CEREBRAS_API_BASE_URL: str = "https://api.cerebras.ai/v1"
    CEREBRAS_MODEL: str = "llama3.1-70b"  # Using Llama 3.1 70B as specified
    
    # Application Configuration
    UPLOAD_DIR: Path = Path("uploads")
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB limit
    ALLOWED_EXTENSIONS: set = {".pdf", ".jpg", ".jpeg", ".png"}
    
    # CORS Configuration
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",  # Live Server default port
        "http://127.0.0.1:5500",
    ]
    
    def __init__(self):
        """Initialize settings and create necessary directories."""
        # Create upload directory if it doesn't exist
        self.UPLOAD_DIR.mkdir(exist_ok=True)
    
    def validate(self) -> tuple[bool, str]:
        """
        Validate required configuration.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.CEREBRAS_API_KEY:
            return False, "CEREBRAS_API_KEY not found in environment variables"
        return True, ""


# Global settings instance
settings = Settings()
