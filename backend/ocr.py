"""
OCR module for extracting text from invoice images and PDFs.
Uses EasyOCR for text extraction and pdf2image for PDF processing.
"""

import re
from pathlib import Path
from typing import Optional
import easyocr
from PIL import Image
from pdf2image import convert_from_path


class OCRProcessor:
    """Handles OCR text extraction from images and PDFs."""
    
    def __init__(self):
        """Initialize EasyOCR reader with English language support."""
        # Initialize EasyOCR with English support
        # Using GPU if available, otherwise CPU
        self.reader = easyocr.Reader(['en'], gpu=False)
    
    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text from an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text as string
            
        Raises:
            Exception: If OCR processing fails
        """
        try:
            # Read text from image
            results = self.reader.readtext(image_path)
            
            # Extract text from results (results is list of tuples: (bbox, text, confidence))
            text_lines = [result[1] for result in results]
            
            # Join lines with newlines
            full_text = '\n'.join(text_lines)
            
            return full_text
        
        except Exception as e:
            raise Exception(f"Failed to extract text from image: {str(e)}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file by converting to images first.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as string
            
        Raises:
            Exception: If PDF processing or OCR fails
        """
        try:
            # Convert PDF to images (one per page)
            images = convert_from_path(pdf_path)
            
            all_text = []
            
            # Process each page
            for i, image in enumerate(images):
                # Save image temporarily
                temp_image_path = f"temp_page_{i}.png"
                image.save(temp_image_path, 'PNG')
                
                # Extract text from this page
                page_text = self.extract_text_from_image(temp_image_path)
                all_text.append(page_text)
                
                # Clean up temporary image
                Path(temp_image_path).unlink(missing_ok=True)
            
            # Combine all pages
            full_text = '\n\n--- PAGE BREAK ---\n\n'.join(all_text)
            
            return full_text
        
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def process_file(self, file_path: str) -> str:
        """
        Process a file (PDF or image) and extract text.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Cleaned extracted text
            
        Raises:
            Exception: If file type is unsupported or processing fails
        """
        file_path_obj = Path(file_path)
        file_extension = file_path_obj.suffix.lower()
        
        # Route to appropriate extraction method
        if file_extension == '.pdf':
            raw_text = self.extract_text_from_pdf(file_path)
        elif file_extension in ['.jpg', '.jpeg', '.png']:
            raw_text = self.extract_text_from_image(file_path)
        else:
            raise Exception(f"Unsupported file type: {file_extension}")
        
        # Clean and normalize the text
        cleaned_text = self.clean_text(raw_text)
        
        return cleaned_text
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace on each line
        lines = [line.strip() for line in text.split('\n')]
        
        # Remove empty lines
        lines = [line for line in lines if line]
        
        # Rejoin with single newlines
        cleaned = '\n'.join(lines)
        
        return cleaned.strip()
