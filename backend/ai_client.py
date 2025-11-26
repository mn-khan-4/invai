"""
Cerebras AI client for invoice data extraction.
Uses Llama 3.1 70B to analyze OCR text and extract structured invoice data.
"""

import json
import httpx
from typing import Optional
from config import settings
from models import InvoiceData


class CerebrasClient:
    """Client for interacting with Cerebras API."""
    
    def __init__(self):
        """Initialize Cerebras client with API configuration."""
        self.api_key = settings.CEREBRAS_API_KEY
        self.base_url = settings.CEREBRAS_API_BASE_URL
        self.model = settings.CEREBRAS_MODEL
        
        if not self.api_key:
            raise ValueError("CEREBRAS_API_KEY is not set")
    
    def _build_system_prompt(self) -> str:
        """
        Build the system prompt that instructs the model how to extract invoice data.
        
        Returns:
            System prompt string
        """
        return """You are an expert invoice analysis AI. Your task is to extract structured information from invoice text that has been obtained via OCR.

CRITICAL REQUIREMENTS:
1. You MUST perform ALL calculations yourself (subtotals, tax amounts, totals, line item totals)
2. Verify that all numbers are mathematically correct and consistent
3. If a field is not present in the invoice, use null (do not guess or hallucinate data)
4. Return ONLY valid JSON with no additional text or explanation
5. Support various currencies and tax formats (GST, VAT, Sales Tax, etc.)

FIELD DESCRIPTIONS:
- supplier_name: The name of the company/vendor issuing the invoice
- supplier_abn_or_vat: Tax identification number (ABN, VAT, EIN, etc.)
- supplier_address: Full address of the supplier
- invoice_number: Unique invoice identifier
- issue_date: Date when invoice was issued (format: YYYY-MM-DD if possible)
- due_date: Payment due date (format: YYYY-MM-DD if possible)
- currency: Currency code (USD, EUR, AUD, GBP, etc.)
- subtotal: Total before tax (YOU must calculate this)
- tax_amount: Total tax amount (YOU must calculate this)
- tax_rate: Tax percentage rate
- total_amount: Final amount due (YOU must calculate: subtotal + tax_amount)
- line_items: Array of items with:
  - description: Item name/description
  - quantity: Number of units (if "Supplied" is empty, use null)
  - unit_price: Price per unit
  - line_total: Total for this line (YOU must calculate: quantity × unit_price)
- notes: Any additional terms, conditions, or notes

CALCULATION RULES:
- line_total = quantity × unit_price
- subtotal = sum of all line_totals
- tax_amount = subtotal × (tax_rate / 100)
- total_amount = subtotal + tax_amount

Ensure all calculations are accurate and the numbers reconcile correctly."""
    
    def _build_user_prompt(self, ocr_text: str) -> str:
        """
        Build the user prompt with the OCR text.
        
        Args:
            ocr_text: Text extracted from invoice via OCR
            
        Returns:
            User prompt string
        """
        return f"""Extract all invoice information from the following OCR text and return it as a JSON object.

OCR TEXT:
{ocr_text}

Return ONLY the JSON object with this exact structure (use null for missing fields):
{{
  "supplier_name": "string or null",
  "supplier_abn_or_vat": "string or null",
  "supplier_address": "string or null",
  "invoice_number": "string or null",
  "issue_date": "string or null",
  "due_date": "string or null",
  "currency": "string",
  "subtotal": number or null,
  "tax_amount": number or null,
  "tax_rate": number or null,
  "total_amount": number or null,
  "line_items": [
    {{
      "description": "string or null",
      "quantity": number or null,
      "unit_price": number or null,
      "line_total": number or null
    }}
  ],
  "notes": "string or null"
}}

Remember: Perform ALL calculations yourself and ensure mathematical consistency."""
    
    async def extract_invoice_data(self, ocr_text: str) -> InvoiceData:
        """
        Send OCR text to Cerebras and get structured invoice data.
        
        Args:
            ocr_text: Text extracted from invoice
            
        Returns:
            InvoiceData object with extracted information
            
        Raises:
            Exception: If API request fails or response is invalid
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(ocr_text)
        
        # Prepare API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,  # Low temperature for consistent, factual extraction
            "max_tokens": 2000,
            "response_format": {"type": "json_object"}  # Force JSON output
        }
        
        try:
            # Make API request
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                
                # Parse response
                result = response.json()
                
                # Extract the message content
                if "choices" not in result or len(result["choices"]) == 0:
                    raise Exception("Invalid response from Cerebras API: no choices")
                
                content = result["choices"][0]["message"]["content"]
                
                # Parse JSON content
                invoice_dict = json.loads(content)
                
                # Validate and convert to InvoiceData model
                invoice_data = InvoiceData(**invoice_dict)
                
                return invoice_data
        
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            raise Exception(f"Cerebras API error: {e.response.status_code} - {error_detail}")
        
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response from Cerebras: {str(e)}")
        
        except Exception as e:
            raise Exception(f"Failed to extract invoice data: {str(e)}")
