"""
Pydantic models for data validation and serialization.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class LineItem(BaseModel):
    """Represents a single line item in an invoice."""
    
    description: Optional[str] = Field(None, description="Item description")
    quantity: Optional[float] = Field(None, description="Quantity ordered/supplied")
    unit_price: Optional[float] = Field(None, description="Price per unit")
    line_total: Optional[float] = Field(None, description="Total for this line item")


class InvoiceData(BaseModel):
    """Complete invoice data structure."""
    
    # Supplier Information
    supplier_name: Optional[str] = Field(None, description="Name of the supplier/vendor")
    supplier_abn_or_vat: Optional[str] = Field(None, description="Supplier ABN or VAT number")
    supplier_address: Optional[str] = Field(None, description="Supplier address")
    
    # Invoice Details
    invoice_number: Optional[str] = Field(None, description="Invoice number")
    issue_date: Optional[str] = Field(None, description="Invoice issue date")
    due_date: Optional[str] = Field(None, description="Payment due date")
    
    # Financial Information
    currency: Optional[str] = Field("USD", description="Currency code (e.g., USD, EUR, AUD)")
    subtotal: Optional[float] = Field(None, description="Subtotal before tax")
    tax_amount: Optional[float] = Field(None, description="Total tax amount")
    tax_rate: Optional[float] = Field(None, description="Tax rate percentage")
    total_amount: Optional[float] = Field(None, description="Final total amount")
    
    # Line Items
    line_items: List[LineItem] = Field(default_factory=list, description="List of invoice line items")
    
    # Additional Information
    notes: Optional[str] = Field(None, description="Any additional notes or terms")


class APIResponse(BaseModel):
    """Standardized API response wrapper."""
    
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[InvoiceData] = Field(None, description="Invoice data if successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    ocr_text: Optional[str] = Field(None, description="Raw OCR text for debugging")
