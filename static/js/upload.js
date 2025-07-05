class PDFUploader {
    constructor() {
        this.form = document.getElementById('uploadForm');
        this.fileInput = document.getElementById('pdfFile');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.uploadSpinner = document.getElementById('uploadSpinner');
        this.uploadProgress = document.getElementById('uploadProgress');
        this.uploadResult = document.getElementById('uploadResult');
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        this.form.addEventListener('submit', (e) => this.handleUpload(e));
        this.fileInput.addEventListener('change', (e) => this.validateFile(e));
    }
    
    validateFile(event) {
        const file = event.target.files[0];
        const maxSize = 10 * 1024 * 1024; // 10MB
        
        if (!file) return;
        
        // Check file type
        if (!file.type.includes('pdf')) {
            this.showError('Please select a PDF file.');
            this.fileInput.value = '';
            return;
        }
        
        // Check file size
        if (file.size > maxSize) {
            this.showError('File size must be less than 10MB.');
            this.fileInput.value = '';
            return;
        }
        
        this.clearMessages();
    }
    
    async handleUpload(event) {
        event.preventDefault();
        
        const formData = new FormData(this.form);
        const file = this.fileInput.files[0];
        
        if (!file) {
            this.showError('Please select a file to upload.');
            return;
        }
        
        this.setUploadingState(true);
        
        try {
            const response = await fetch('/upload-pdf', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showSuccess(result);
                // Redirect to display page after 2 seconds
                setTimeout(() => {
                    window.location.href = `/display/${result.session_id}`;
                }, 2000);
            } else {
                this.showError(result.detail || 'Upload failed.');
            }
        } catch (error) {
            this.showError('Network error. Please try again.');
            console.error('Upload error:', error);
        } finally {
            this.setUploadingState(false);
        }
    }
    
    setUploadingState(uploading) {
        this.uploadBtn.disabled = uploading;
        this.uploadSpinner.classList.toggle('d-none', !uploading);
        this.uploadProgress.classList.toggle('d-none', !uploading);
        
        if (uploading) {
            this.uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading...';
        } else {
            this.uploadBtn.innerHTML = 'Upload Document';
        }
    }
    
    showSuccess(result) {
        this.uploadResult.innerHTML = `
            <div class="alert alert-success">
                <h5><i class="fas fa-check-circle me-2"></i>Upload Successful!</h5>
                <p><strong>File:</strong> ${result.file_name}</p>
                <p><strong>Type:</strong> ${result.file_type.replace('_', ' ').toUpperCase()}</p>
                <p>Redirecting to document viewer...</p>
            </div>
        `;
    }
    
    showError(message) {
        this.uploadResult.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
    }
    
    clearMessages() {
        this.uploadResult.innerHTML = '';
    }
}

// Initialize uploader when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PDFUploader();
}); 