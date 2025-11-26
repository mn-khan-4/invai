/**
 * InvoiceAI Frontend Application
 * Handles file upload, API communication, and result display
 */

// API Configuration
const API_BASE_URL = 'http://localhost:8000';
const API_ENDPOINT = `${API_BASE_URL}/api/invoice/extract`;

// DOM Elements
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const filePreview = document.getElementById('filePreview');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const removeBtn = document.getElementById('removeBtn');
const extractBtn = document.getElementById('extractBtn');
const loadingState = document.getElementById('loadingState');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');
const resultsSection = document.getElementById('resultsSection');
const invoiceSummary = document.getElementById('invoiceSummary');
const jsonOutput = document.getElementById('jsonOutput');
const toggleJsonBtn = document.getElementById('toggleJsonBtn');

// State
let selectedFile = null;

/* ===================================
   File Upload Handlers
   =================================== */

// Click to upload
uploadZone.addEventListener('click', () => {
    fileInput.click();
});

// File input change
fileInput.addEventListener('change', (e) => {
    handleFileSelect(e.target.files[0]);
});

// Drag and drop
uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('drag-over');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    handleFileSelect(e.dataTransfer.files[0]);
});

// Remove file
removeBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    clearFile();
});

/**
 * Handle file selection
 */
function handleFileSelect(file) {
    if (!file) return;
    
    // Validate file type
    const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
    if (!validTypes.includes(file.type)) {
        showError('Invalid file type. Please upload a PDF, JPG, or PNG file.');
        return;
    }
    
    // Validate file size (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('File is too large. Maximum size is 10MB.');
        return;
    }
    
    selectedFile = file;
    
    // Update UI
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    
    uploadZone.style.display = 'none';
    filePreview.style.display = 'flex';
    extractBtn.disabled = false;
    
    // Clear previous results/errors
    hideError();
    hideResults();
}

/**
 * Clear selected file
 */
function clearFile() {
    selectedFile = null;
    fileInput.value = '';
    
    uploadZone.style.display = 'block';
    filePreview.style.display = 'none';
    extractBtn.disabled = true;
    
    hideError();
    hideResults();
}

/* ===================================
   Extract Invoice Handler
   =================================== */

extractBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    // Show loading state
    showLoading();
    hideError();
    hideResults();
    
    try {
        // Prepare form data
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        // Make API request
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        hideLoading();
        
        if (result.success && result.data) {
            // Display results
            displayInvoiceSummary(result.data);
            displayJSON(result.data);
            showResults();
        } else {
            // Show error
            showError(result.error || 'Failed to extract invoice data');
        }
    } catch (error) {
        hideLoading();
        showError(`Network error: ${error.message}. Make sure the backend server is running.`);
    }
});

/* ===================================
   Display Functions
   =================================== */

/**
 * Display invoice summary
 */
function displayInvoiceSummary(data) {
    const html = `
        <!-- Supplier Information -->
        <div class="invoice-section">
            <div class="section-title">Supplier Information</div>
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Supplier Name</span>
                    <span class="info-value">${data.supplier_name || 'N/A'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">ABN/VAT</span>
                    <span class="info-value">${data.supplier_abn_or_vat || 'N/A'}</span>
                </div>
                ${data.supplier_address ? `
                <div class="info-item" style="grid-column: 1 / -1;">
                    <span class="info-label">Address</span>
                    <span class="info-value">${data.supplier_address}</span>
                </div>
                ` : ''}
            </div>
        </div>

        <!-- Invoice Details -->
        <div class="invoice-section">
            <div class="section-title">Invoice Details</div>
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Invoice Number</span>
                    <span class="info-value">${data.invoice_number || 'N/A'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Issue Date</span>
                    <span class="info-value">${formatDate(data.issue_date)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Due Date</span>
                    <span class="info-value">${formatDate(data.due_date)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Currency</span>
                    <span class="info-value">${data.currency || 'USD'}</span>
                </div>
            </div>
        </div>

        <!-- Financial Summary -->
        <div class="invoice-section">
            <div class="section-title">Financial Summary</div>
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Subtotal</span>
                    <span class="info-value">${formatCurrency(data.subtotal, data.currency)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Tax (${data.tax_rate || 0}%)</span>
                    <span class="info-value">${formatCurrency(data.tax_amount, data.currency)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Total Amount</span>
                    <span class="info-value highlight">${formatCurrency(data.total_amount, data.currency)}</span>
                </div>
            </div>
        </div>

        <!-- Line Items -->
        ${data.line_items && data.line_items.length > 0 ? `
        <div class="invoice-section">
            <div class="section-title">Line Items</div>
            <table class="line-items-table">
                <thead>
                    <tr>
                        <th>Description</th>
                        <th class="text-right">Quantity</th>
                        <th class="text-right">Unit Price</th>
                        <th class="text-right">Total</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.line_items.map(item => `
                        <tr>
                            <td>${item.description || 'N/A'}</td>
                            <td class="text-right">${item.quantity !== null && item.quantity !== undefined ? item.quantity : 'N/A'}</td>
                            <td class="text-right">${formatCurrency(item.unit_price, data.currency)}</td>
                            <td class="text-right">${formatCurrency(item.line_total, data.currency)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        ` : ''}

        <!-- Notes -->
        ${data.notes ? `
        <div class="invoice-section">
            <div class="section-title">Notes</div>
            <p class="info-value">${data.notes}</p>
        </div>
        ` : ''}
    `;
    
    invoiceSummary.innerHTML = html;
}

/**
 * Display JSON output
 */
function displayJSON(data) {
    jsonOutput.textContent = JSON.stringify(data, null, 2);
}

/* ===================================
   UI State Management
   =================================== */

function showLoading() {
    loadingState.style.display = 'block';
}

function hideLoading() {
    loadingState.style.display = 'none';
}

function showError(message) {
    errorText.textContent = message;
    errorMessage.style.display = 'block';
}

function hideError() {
    errorMessage.style.display = 'none';
}

function showResults() {
    resultsSection.style.display = 'block';
}

function hideResults() {
    resultsSection.style.display = 'none';
}

/* ===================================
   Toggle JSON Display
   =================================== */

toggleJsonBtn.addEventListener('click', () => {
    const isVisible = jsonOutput.style.display !== 'none';
    
    if (isVisible) {
        jsonOutput.style.display = 'none';
        toggleJsonBtn.textContent = 'Show';
    } else {
        jsonOutput.style.display = 'block';
        toggleJsonBtn.textContent = 'Hide';
    }
});

/* ===================================
   Utility Functions
   =================================== */

/**
 * Format file size in human-readable format
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Format currency
 */
function formatCurrency(amount, currency = 'USD') {
    if (amount === null || amount === undefined) return 'N/A';
    
    try {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    } catch (e) {
        // Fallback if currency code is invalid
        return `${currency} ${amount.toFixed(2)}`;
    }
}

/**
 * Format date
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return dateString; // Return original if invalid
        
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } catch (e) {
        return dateString;
    }
}
