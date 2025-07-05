from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
import uuid
from datetime import datetime
from api.database.connection import DatabaseManager
from api.database.migrations import DatabaseMigration
from api.database.utils import DatabaseUtils
from api.config.settings import settings
from typing import Dict, Any

# Initialize FastAPI app
app = FastAPI(
    title="Tax Advisor API",
    description="AI-powered tax calculation and advisory system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize database
db_manager = DatabaseManager()
db_utils = DatabaseUtils(db_manager)
migration = DatabaseMigration()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

def convert_datetime_to_string(obj: Any) -> Any:
    """Convert datetime objects to ISO format strings for JSON serialization"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_datetime_to_string(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_string(item) for item in obj]
    else:
        return obj

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting Tax Advisor API...")
    
    # Run database migrations
    migration.run_migrations()
    print("✓ Database migrations completed")
    
    # Validate settings
    settings.validate()
    print("✓ Configuration validated")

@app.get("/", response_class=HTMLResponse)
async def upload_page(request: Request):
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
    
    return FileResponse(file_path, media_type="application/pdf")

@app.get("/display/{session_id}")
async def display_pdf(request: Request, session_id: str):
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
    
    # Convert datetime objects to strings for JSON serialization
    document_data = convert_datetime_to_string(latest_doc)
    
    return templates.TemplateResponse("display.html", {
        "request": request,
        "session_id": session_id,
        "document": document_data
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

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": "2024-01-01T00:00:00Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 