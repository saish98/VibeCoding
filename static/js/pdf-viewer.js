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