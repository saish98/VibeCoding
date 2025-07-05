# Phase 2: PDF Upload & Display System (Local File System + PDF.js)

## Overview
Phase 2 focuses on implementing the PDF upload and display functionality for the Tax Advisor application. This phase enables users to upload Pay Slips, Salary Slips, or Form 16 documents (image-based PDFs) and view them in the browser while manually entering data. The system uses local file storage during development and PDF.js for in-browser PDF rendering.

## Objectives
- [ ] Implement PDF file upload functionality with validation
- [ ] Create secure file storage system (local file system for development)
- [ ] Integrate PDF.js for in-browser PDF display
- [ ] Build responsive UI for upload and display
- [ ] Implement file type validation and size limits
- [ ] Create session-based file management
- [ ] Add file cleanup and security measures

## Technical Requirements

### File Upload Specifications
- **Supported Formats:** PDF files only
- **File Size Limit:** 10MB maximum
- **File Types:** Pay Slip, Salary Slip, Form 16
- **Storage:** Local file system (`./uploads/` directory)
- **Session Management:** Files linked to user sessions
- **Security:** Temporary storage with automatic cleanup

### PDF Display Requirements
- **Rendering Engine:** PDF.js for client-side rendering
- **Browser Compatibility:** Modern browsers (Chrome, Firefox, Safari, Edge)
- **Responsive Design:** Mobile-friendly PDF viewing
- **Zoom Controls:** Pan and zoom functionality
- **Side-by-side Layout:** PDF display alongside input forms

## Implementation Tasks

### Task 2.1: Project Structure Updates
```
tax-advisor/
├── api/
│   ├── main.py (updated with upload endpoints)
│   ├── uploads/ (new directory for file storage)
│   └── static/
│       ├── pdf.js/ (PDF.js library files)
│       └── upload.js (upload functionality)
├── templates/
│   ├── upload.html (upload interface)
│   └── display.html (PDF display interface)
├── uploads/ (file storage directory)
└── static/
    ├── css/
    │   └── upload.css (upload styling)
    └── js/
        └── pdf-viewer.js (PDF display logic)
```

### Task 2.2: FastAPI Upload Endpoints
**File: `api/main.py` (Updated)**
```python
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
import uuid
from datetime import datetime
from database.utils import DatabaseUtils
from database.connection import DatabaseManager
from config.settings import settings

app = FastAPI(title="Tax Advisor API")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Database setup
db_manager = DatabaseManager()
db_utils = DatabaseUtils(db_manager)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def upload_page(request):
    """Main upload page"""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: str = Form(None)
):
    """Handle PDF file upload"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Validate file size
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    
    # Generate session ID if not provided
    if not session_id:
        session_id = db_utils.create_session()
    
    # Validate session
    if not db_utils.validate_session(session_id):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_FOLDER, unique_filename)
    
    try:
        # Save file to disk
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Determine file type based on filename
        file_type = "pay_slip"  # Default
        filename_lower = file.filename.lower()
        if "form16" in filename_lower or "form_16" in filename_lower:
            file_type = "form_16"
        elif "salary" in filename_lower:
            file_type = "salary_slip"
        
        # Save file metadata to database
        doc_id = db_utils.save_document(
            session_id=session_id,
            file_name=file.filename,
            file_url=f"/uploads/{unique_filename}",
            file_type=file_type
        )
        
        return JSONResponse({
            "success": True,
            "session_id": session_id,
            "document_id": doc_id,
            "file_name": file.filename,
            "file_type": file_type,
            "file_url": f"/uploads/{unique_filename}"
        })
        
    except Exception as e:
        # Clean up file if database save fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/uploads/{filename}")
async def serve_file(filename: str):
    """Serve uploaded files"""
    file_path = os.path.join(settings.UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(file_path, media_type="application/pdf")

@app.get("/display/{session_id}")
async def display_pdf(request, session_id: str):
    """Display uploaded PDF with input forms"""
    
    # Validate session
    if not db_utils.validate_session(session_id):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Get session data
    session_data = db_utils.get_session_data(session_id)
    documents = session_data.get('documents', [])
    
    if not documents:
        raise HTTPException(status_code=404, detail="No documents found for session")
    
    # Get the most recent document
    latest_doc = documents[0]
    
    return templates.TemplateResponse("display.html", {
        "request": request,
        "session_id": session_id,
        "document": latest_doc
    })

@app.delete("/delete-file/{document_id}")
async def delete_file(document_id: int, session_id: str):
    """Delete uploaded file"""
    
    # Validate session
    if not db_utils.validate_session(session_id):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Get document info from database
    with db_manager.get_connection() as conn:
        cursor = conn.execute(
            "SELECT file_url FROM documents WHERE id = ? AND session_id = ?",
            (document_id, session_id)
        )
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_url = result['file_url']
        filename = file_url.split('/')[-1]
        file_path = os.path.join(settings.UPLOAD_FOLDER, filename)
        
        # Delete from database
        conn.execute(
            "DELETE FROM documents WHERE id = ? AND session_id = ?",
            (document_id, session_id)
        )
        conn.commit()
        
        # Delete file from disk
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return JSONResponse({"success": True, "message": "File deleted successfully"})
```

### Task 2.3: HTML Templates
**File: `templates/upload.html`**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tax Advisor - Upload Document</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="/static/css/upload.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card shadow">
                    <div class="card-header bg-primary text-white">
                        <h3 class="mb-0">
                            <i class="fas fa-upload me-2"></i>
                            Upload Your Tax Document
                        </h3>
                    </div>
                    <div class="card-body">
                        <div class="alert alert-info">
                            <strong>Supported Documents:</strong>
                            <ul class="mb-0 mt-2">
                                <li>Pay Slip / Salary Slip</li>
                                <li>Form 16</li>
                            </ul>
                            <small class="text-muted">Maximum file size: 10MB | Format: PDF only</small>
                        </div>
                        
                        <form id="uploadForm" enctype="multipart/form-data">
                            <div class="mb-3">
                                <label for="pdfFile" class="form-label">Select PDF Document</label>
                                <input type="file" class="form-control" id="pdfFile" name="file" 
                                       accept=".pdf" required>
                                <div class="form-text">Choose your Pay Slip, Salary Slip, or Form 16</div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="fileType" class="form-label">Document Type</label>
                                <select class="form-select" id="fileType" name="fileType">
                                    <option value="pay_slip">Pay Slip / Salary Slip</option>
                                    <option value="form_16">Form 16</option>
                                </select>
                            </div>
                            
                            <div class="d-grid">
                                <button type="submit" class="btn btn-primary btn-lg" id="uploadBtn">
                                    <span class="spinner-border spinner-border-sm d-none me-2" id="uploadSpinner"></span>
                                    Upload Document
                                </button>
                            </div>
                        </form>
                        
                        <div id="uploadProgress" class="mt-3 d-none">
                            <div class="progress">
                                <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                            </div>
                            <small class="text-muted">Uploading...</small>
                        </div>
                        
                        <div id="uploadResult" class="mt-3"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/static/js/upload.js"></script>
</body>
</html>
```

**File: `templates/display.html`**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tax Advisor - Document Analysis</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="/static/css/pdf-viewer.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-calculator me-2"></i>
                Tax Advisor
            </a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text">
                    Session: <code>{{ session_id[:8] }}...</code>
                </span>
            </div>
        </div>
    </nav>
    
    <div class="container-fluid mt-3">
        <div class="row">
            <!-- PDF Viewer Column -->
            <div class="col-lg-6">
                <div class="card shadow">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">
                            <i class="fas fa-file-pdf me-2"></i>
                            {{ document.file_name }}
                        </h5>
                        <div class="btn-group" role="group">
                            <button type="button" class="btn btn-sm btn-outline-secondary" id="zoomOut">
                                <i class="fas fa-search-minus"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-secondary" id="zoomIn">
                                <i class="fas fa-search-plus"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-secondary" id="fitWidth">
                                Fit Width
                            </button>
                        </div>
                    </div>
                    <div class="card-body p-0">
                        <div id="pdfContainer" class="pdf-container">
                            <div id="pdfViewer" class="pdf-viewer"></div>
                            <div id="pdfLoading" class="pdf-loading">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p class="mt-2">Loading PDF...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Data Input Column -->
            <div class="col-lg-6">
                <div class="card shadow">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="fas fa-edit me-2"></i>
                            Manual Data Entry
                        </h5>
                        <small class="text-muted">Enter details from your {{ document.file_type.replace('_', ' ').title() }}</small>
                    </div>
                    <div class="card-body">
                        <div id="dataInputForm">
                            <!-- Form will be dynamically generated based on document type -->
                            <div class="text-center">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading form...</span>
                                </div>
                                <p class="mt-2">Loading input form...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Pass data to JavaScript
        window.sessionId = "{{ session_id }}";
        window.documentData = {{ document | tojson }};
    </script>
    <script src="/static/js/pdf-viewer.js"></script>
</body>
</html>
```

### Task 2.4: JavaScript Implementation
**File: `static/js/upload.js`**
```javascript
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
```

**File: `static/js/pdf-viewer.js`**
```javascript
class PDFViewer {
    constructor() {
        this.currentPage = 1;
        this.totalPages = 0;
        this.scale = 1.0;
        this.pdfDoc = null;
        this.pageRendering = false;
        this.pageNumPending = null;
        
        this.container = document.getElementById('pdfViewer');
        this.loadingDiv = document.getElementById('pdfLoading');
        
        this.initializeControls();
        this.loadPDF();
    }
    
    initializeControls() {
        document.getElementById('zoomIn').addEventListener('click', () => this.zoom(1.2));
        document.getElementById('zoomOut').addEventListener('click', () => this.zoom(0.8));
        document.getElementById('fitWidth').addEventListener('click', () => this.fitWidth());
    }
    
    async loadPDF() {
        try {
            const pdfUrl = window.documentData.file_url;
            
            // Load PDF document
            const loadingTask = pdfjsLib.getDocument(pdfUrl);
            this.pdfDoc = await loadingTask.promise;
            
            this.totalPages = this.pdfDoc.numPages;
            this.loadingDiv.style.display = 'none';
            
            // Render first page
            this.renderPage(1);
            
        } catch (error) {
            console.error('Error loading PDF:', error);
            this.loadingDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error loading PDF. Please try again.
                </div>
            `;
        }
    }
    
    async renderPage(pageNum) {
        this.pageRendering = true;
        
        try {
            const page = await this.pdfDoc.getPage(pageNum);
            const viewport = page.getViewport({ scale: this.scale });
            
            // Prepare canvas
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            
            // Clear container
            this.container.innerHTML = '';
            this.container.appendChild(canvas);
            
            // Render PDF page
            const renderContext = {
                canvasContext: context,
                viewport: viewport
            };
            
            await page.render(renderContext).promise;
            this.currentPage = pageNum;
            
        } catch (error) {
            console.error('Error rendering page:', error);
        } finally {
            this.pageRendering = false;
            
            // Render pending page if any
            if (this.pageNumPending !== null) {
                this.renderPage(this.pageNumPending);
                this.pageNumPending = null;
            }
        }
    }
    
    zoom(factor) {
        this.scale *= factor;
        this.scale = Math.max(0.5, Math.min(3.0, this.scale)); // Limit zoom range
        this.renderPage(this.currentPage);
    }
    
    fitWidth() {
        if (!this.pdfDoc) return;
        
        const containerWidth = this.container.clientWidth;
        this.pdfDoc.getPage(1).then(page => {
            const viewport = page.getViewport({ scale: 1.0 });
            this.scale = containerWidth / viewport.width;
            this.renderPage(this.currentPage);
        });
    }
    
    queueRenderPage(pageNum) {
        if (this.pageRendering) {
            this.pageNumPending = pageNum;
        } else {
            this.renderPage(pageNum);
        }
    }
}

// Initialize PDF viewer when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Set PDF.js worker path
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    
    new PDFViewer();
});
```

### Task 2.5: CSS Styling
**File: `static/css/upload.css`**
```css
.card {
    border: none;
    border-radius: 15px;
}

.card-header {
    border-radius: 15px 15px 0 0 !important;
    border-bottom: none;
}

.form-control, .form-select {
    border-radius: 10px;
    border: 2px solid #e9ecef;
    transition: border-color 0.3s ease;
}

.form-control:focus, .form-select:focus {
    border-color: #0d6efd;
    box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
}

.btn {
    border-radius: 10px;
    font-weight: 600;
    transition: all 0.3s ease;
}

.btn-primary {
    background: linear-gradient(45deg, #0d6efd, #0b5ed7);
    border: none;
}

.btn-primary:hover {
    background: linear-gradient(45deg, #0b5ed7, #0a58ca);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(13, 110, 253, 0.3);
}

.progress {
    border-radius: 10px;
    height: 8px;
}

.progress-bar {
    background: linear-gradient(45deg, #0d6efd, #0b5ed7);
}

.alert {
    border-radius: 10px;
    border: none;
}

.upload-area {
    border: 2px dashed #dee2e6;
    border-radius: 15px;
    padding: 40px;
    text-align: center;
    transition: border-color 0.3s ease;
    cursor: pointer;
}

.upload-area:hover {
    border-color: #0d6efd;
    background-color: #f8f9fa;
}

.upload-area.dragover {
    border-color: #0d6efd;
    background-color: #e7f3ff;
}
```

**File: `static/css/pdf-viewer.css`**
```css
.pdf-container {
    position: relative;
    min-height: 600px;
    background-color: #f8f9fa;
    border-radius: 10px;
    overflow: hidden;
}

.pdf-viewer {
    width: 100%;
    height: 100%;
    min-height: 600px;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 20px;
    overflow: auto;
}

.pdf-viewer canvas {
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    border-radius: 8px;
    max-width: 100%;
    height: auto;
}

.pdf-loading {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    color: #6c757d;
}

.btn-group .btn {
    border-radius: 6px;
    margin: 0 2px;
}

.btn-group .btn:hover {
    background-color: #e9ecef;
}

.navbar-brand {
    font-weight: 700;
    font-size: 1.5rem;
}

.navbar-text code {
    background-color: rgba(255, 255, 255, 0.2);
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.9rem;
}

.card {
    border: none;
    border-radius: 15px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.card-header {
    background: linear-gradient(45deg, #f8f9fa, #e9ecef);
    border-bottom: 1px solid #dee2e6;
    border-radius: 15px 15px 0 0 !important;
}

/* Responsive design */
@media (max-width: 768px) {
    .pdf-container {
        min-height: 400px;
    }
    
    .pdf-viewer {
        min-height: 400px;
        padding: 10px;
    }
    
    .btn-group .btn {
        padding: 0.25rem 0.5rem;
        font-size: 0.875rem;
    }
}
```

### Task 2.6: Database Schema Updates
The existing database schema from Phase 1 already supports document storage. No additional schema changes are needed.

### Task 2.7: File Cleanup System
**File: `api/utils/cleanup.py`**
```python
import os
import schedule
import time
from datetime import datetime, timedelta
from database.connection import DatabaseManager
from database.utils import DatabaseUtils
from config.settings import settings

class FileCleanupService:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.db_utils = DatabaseUtils(self.db_manager)
    
    def cleanup_expired_files(self):
        """Remove files associated with expired sessions"""
        try:
            # Clean up expired sessions (this also removes related files)
            expired_count = self.db_utils.cleanup_expired_sessions()
            
            # Additional cleanup: Remove orphaned files
            orphaned_files = self.find_orphaned_files()
            for file_path in orphaned_files:
                try:
                    os.remove(file_path)
                    print(f"Removed orphaned file: {file_path}")
                except Exception as e:
                    print(f"Failed to remove orphaned file {file_path}: {e}")
            
            print(f"Cleanup completed: {expired_count} expired sessions, {len(orphaned_files)} orphaned files")
            
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def find_orphaned_files(self):
        """Find files in upload directory that are not in database"""
        orphaned = []
        
        if not os.path.exists(settings.UPLOAD_FOLDER):
            return orphaned
        
        # Get all files in upload directory
        upload_files = set()
        for filename in os.listdir(settings.UPLOAD_FOLDER):
            file_path = os.path.join(settings.UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                upload_files.add(filename)
        
        # Get files referenced in database
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT file_url FROM documents")
            db_files = set()
            for row in cursor.fetchall():
                filename = row['file_url'].split('/')[-1]
                db_files.add(filename)
        
        # Find orphaned files
        orphaned_filenames = upload_files - db_files
        
        for filename in orphaned_filenames:
            file_path = os.path.join(settings.UPLOAD_FOLDER, filename)
            orphaned.append(file_path)
        
        return orphaned

def run_cleanup_service():
    """Run the cleanup service"""
    cleanup_service = FileCleanupService()
    
    # Schedule cleanup every hour
    schedule.every().hour.do(cleanup_service.cleanup_expired_files)
    
    print("File cleanup service started. Running every hour.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    run_cleanup_service()
```

## Testing & Validation

### Test 2.1: File Upload Test
```python
# test_upload.py
import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_pdf_upload():
    """Test PDF file upload functionality"""
    
    # Create a test PDF file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp.write(b'%PDF-1.4\n%Test PDF content')
        tmp_path = tmp.name
    
    try:
        with open(tmp_path, 'rb') as f:
            response = client.post(
                '/upload-pdf',
                files={'file': ('test.pdf', f, 'application/pdf')},
                data={'fileType': 'pay_slip'}
            )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] == True
        assert 'session_id' in result
        assert 'document_id' in result
        
    finally:
        os.unlink(tmp_path)

def test_invalid_file_type():
    """Test upload with invalid file type"""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
        tmp.write(b'This is not a PDF')
        tmp_path = tmp.name
    
    try:
        with open(tmp_path, 'rb') as f:
            response = client.post(
                '/upload-pdf',
                files={'file': ('test.txt', f, 'text/plain')}
            )
        
        assert response.status_code == 400
        assert 'Only PDF files are allowed' in response.json()['detail']
        
    finally:
        os.unlink(tmp_path)
```

### Test 2.2: PDF Display Test
```python
def test_pdf_display():
    """Test PDF display page"""
    # First upload a PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp.write(b'%PDF-1.4\n%Test PDF content')
        tmp_path = tmp.name
    
    try:
        with open(tmp_path, 'rb') as f:
            upload_response = client.post(
                '/upload-pdf',
                files={'file': ('test.pdf', f, 'application/pdf')}
            )
        
        upload_result = upload_response.json()
        session_id = upload_result['session_id']
        
        # Test display page
        display_response = client.get(f'/display/{session_id}')
        assert display_response.status_code == 200
        assert 'PDF Viewer' in display_response.text
        
    finally:
        os.unlink(tmp_path)
```

## Deliverables Checklist

- [ ] **Upload Endpoints**: FastAPI endpoints for file upload and management
- [ ] **File Storage**: Local file system storage with session-based organization
- [ ] **PDF Display**: PDF.js integration for in-browser PDF viewing
- [ ] **Upload Interface**: Responsive HTML form for file upload
- [ ] **Display Interface**: Side-by-side PDF viewer and data input layout
- [ ] **File Validation**: Type and size validation for uploaded files
- [ ] **Session Management**: File linking to user sessions
- [ ] **Security Measures**: File cleanup and access control
- [ ] **Error Handling**: Comprehensive error handling and user feedback
- [ ] **Testing**: Unit tests for upload and display functionality

## Success Criteria

1. **File Upload**: Users can successfully upload PDF files up to 10MB
2. **File Validation**: Only PDF files are accepted with proper error messages
3. **PDF Display**: Uploaded PDFs render correctly in the browser
4. **Session Management**: Files are properly linked to user sessions
5. **Security**: Files are stored securely with proper access controls
6. **Cleanup**: Expired sessions and orphaned files are cleaned up automatically
7. **Responsive Design**: Interface works well on desktop and mobile devices
8. **Error Handling**: Graceful handling of upload failures and display errors

## Next Phase Preparation

Phase 2 completion enables:
- **Phase 3**: Manual data input forms can reference uploaded PDFs
- [ ] **Phase 4**: Tax calculations can use data from uploaded documents
- [ ] **Phase 5**: AI suggestions can reference document content
- [ ] **Phase 6**: Chat system can provide context-aware advice
- [ ] **Phase 7**: Complete application with full document workflow

## Estimated Timeline
- **Upload Endpoints**: 4 hours
- **PDF Display Integration**: 6 hours
- **Frontend Interface**: 8 hours
- **File Management**: 3 hours
- **Security & Cleanup**: 2 hours
- **Testing**: 4 hours
- **Documentation**: 2 hours

**Total Estimated Time: 29 hours**

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|-------------------|
| Large file uploads | Implement file size limits and progress indicators |
| PDF rendering issues | Use PDF.js with fallback error handling |
| File storage security | Implement session-based access and automatic cleanup |
| Browser compatibility | Test across major browsers and provide fallbacks |
| Memory usage | Implement lazy loading and cleanup for large PDFs |
| Network timeouts | Add retry logic and timeout handling |

---

**Phase 2 Goal**: Complete PDF upload and display system with secure file handling, responsive interface, and robust error management for the Tax Advisor application. 