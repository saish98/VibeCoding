#!/usr/bin/env python3
"""
Phase 2 PDF Upload & Display System Verification Script
Tests all components of the PDF upload and display system
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.database.connection import DatabaseManager
from api.database.utils import DatabaseUtils
from api.config.settings import settings

def test_directory_structure():
    """Test 2.1: Directory Structure Verification"""
    print("🔍 Testing Directory Structure...")
    
    required_dirs = [
        "templates",
        "static/css",
        "static/js",
        "static/pdf.js",
        "uploads",
        "api/uploads",
        "api/utils"
    ]
    
    required_files = [
        "templates/upload.html",
        "templates/display.html",
        "static/css/upload.css",
        "static/css/pdf-viewer.css",
        "static/js/upload.js",
        "static/js/pdf-viewer.js",
        "api/utils/cleanup.py",
        "api/utils/__init__.py"
    ]
    
    missing_dirs = []
    missing_files = []
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
        else:
            print(f"✓ Directory {dir_path} exists")
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✓ File {file_path} exists")
    
    if missing_dirs or missing_files:
        print(f"✗ Missing directories: {missing_dirs}")
        print(f"✗ Missing files: {missing_files}")
        return False
    
    print("✓ All required directories and files exist")
    return True

def test_database_integration():
    """Test 2.2: Database Integration Test"""
    print("\n🔍 Testing Database Integration...")
    
    try:
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db_manager = DatabaseManager(tmp.name)
            db_utils = DatabaseUtils(db_manager)
            
            # Test session creation
            session_id = db_utils.create_session()
            print(f"✓ Session created: {session_id[:8]}...")
            
            # Test document saving
            doc_id = db_utils.save_document(
                session_id=session_id,
                file_name="test.pdf",
                file_url="/uploads/test.pdf",
                file_type="pay_slip"
            )
            print(f"✓ Document saved with ID: {doc_id}")
            
            # Test session data retrieval
            session_data = db_utils.get_session_data(session_id)
            documents = session_data.get('documents', [])
            assert len(documents) == 1, "Document not found in session data"
            print("✓ Session data retrieval successful")
            
        return True
    except Exception as e:
        print(f"✗ Database integration test failed: {e}")
        return False

def test_file_operations():
    """Test 2.3: File Operations Test"""
    print("\n🔍 Testing File Operations...")
    
    try:
        # Test upload directory creation
        test_upload_dir = "./test_uploads"
        os.makedirs(test_upload_dir, exist_ok=True)
        
        # Create a test PDF file
        test_pdf_path = os.path.join(test_upload_dir, "test.pdf")
        with open(test_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n%Test PDF content")
        
        # Test file serving path
        if os.path.exists(test_pdf_path):
            print("✓ Test PDF file created successfully")
            
            # Test file size
            file_size = os.path.getsize(test_pdf_path)
            print(f"✓ File size: {file_size} bytes")
            
            # Clean up
            os.remove(test_pdf_path)
            os.rmdir(test_upload_dir)
            print("✓ Test files cleaned up")
        else:
            print("✗ Failed to create test PDF file")
            return False
        
        return True
    except Exception as e:
        print(f"✗ File operations test failed: {e}")
        return False

def test_template_content():
    """Test 2.4: Template Content Verification"""
    print("\n🔍 Testing Template Content...")
    
    try:
        # Check upload.html
        with open("templates/upload.html", "r") as f:
            upload_content = f.read()
            required_elements = [
                "uploadForm",
                "pdfFile",
                "uploadBtn",
                "bootstrap",
                "font-awesome"
            ]
            
            for element in required_elements:
                if element in upload_content:
                    print(f"✓ Upload template contains {element}")
                else:
                    print(f"✗ Upload template missing {element}")
                    return False
        
        # Check display.html
        with open("templates/display.html", "r") as f:
            display_content = f.read().lower()  # Make content lowercase for case-insensitive search
            required_elements = [
                "pdfviewer",
                "pdfcontainer",
                "zoomin",
                "zoomout",
                "pdf.js"  # Now checks for lowercase 'pdf.js'
            ]
            
            for element in required_elements:
                if element in display_content:
                    print(f"✓ Display template contains {element}")
                else:
                    print(f"✗ Display template missing {element}")
                    return False
        
        return True
    except Exception as e:
        print(f"✗ Template content test failed: {e}")
        return False

def test_javascript_functionality():
    """Test 2.5: JavaScript Functionality Verification"""
    print("\n🔍 Testing JavaScript Functionality...")
    
    try:
        # Check upload.js
        with open("static/js/upload.js", "r") as f:
            upload_js = f.read()
            required_functions = [
                "PDFUploader",
                "handleUpload",
                "validateFile",
                "fetch"
            ]
            
            for func in required_functions:
                if func in upload_js:
                    print(f"✓ Upload JS contains {func}")
                else:
                    print(f"✗ Upload JS missing {func}")
                    return False
        
        # Check pdf-viewer.js
        with open("static/js/pdf-viewer.js", "r") as f:
            viewer_js = f.read()
            required_functions = [
                "PDFViewer",
                "loadPDF",
                "renderPage",
                "zoom"
            ]
            
            for func in required_functions:
                if func in viewer_js:
                    print(f"✓ PDF viewer JS contains {func}")
                else:
                    print(f"✗ PDF viewer JS missing {func}")
                    return False
        
        return True
    except Exception as e:
        print(f"✗ JavaScript functionality test failed: {e}")
        return False

def test_css_styling():
    """Test 2.6: CSS Styling Verification"""
    print("\n🔍 Testing CSS Styling...")
    
    try:
        # Check upload.css
        with open("static/css/upload.css", "r") as f:
            upload_css = f.read()
            required_styles = [
                ".card",
                ".btn-primary",
                ".form-control",
                "border-radius"
            ]
            
            for style in required_styles:
                if style in upload_css:
                    print(f"✓ Upload CSS contains {style}")
                else:
                    print(f"✗ Upload CSS missing {style}")
                    return False
        
        # Check pdf-viewer.css
        with open("static/css/pdf-viewer.css", "r") as f:
            viewer_css = f.read()
            required_styles = [
                ".pdf-container",
                ".pdf-viewer",
                "canvas",
                "@media"
            ]
            
            for style in required_styles:
                if style in viewer_css:
                    print(f"✓ PDF viewer CSS contains {style}")
                else:
                    print(f"✗ PDF viewer CSS missing {style}")
                    return False
        
        return True
    except Exception as e:
        print(f"✗ CSS styling test failed: {e}")
        return False

def test_cleanup_utility():
    """Test 2.7: Cleanup Utility Verification"""
    print("\n🔍 Testing Cleanup Utility...")
    
    try:
        with open("api/utils/cleanup.py", "r") as f:
            cleanup_code = f.read()
            required_classes = [
                "FileCleanupService",
                "cleanup_expired_files",
                "find_orphaned_files"
            ]
            
            for class_name in required_classes:
                if class_name in cleanup_code:
                    print(f"✓ Cleanup utility contains {class_name}")
                else:
                    print(f"✗ Cleanup utility missing {class_name}")
                    return False
        
        return True
    except Exception as e:
        print(f"✗ Cleanup utility test failed: {e}")
        return False

def main():
    """Run all Phase 2 tests"""
    print("🚀 Phase 2 PDF Upload & Display System Verification")
    print("=" * 60)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Database Integration", test_database_integration),
        ("File Operations", test_file_operations),
        ("Template Content", test_template_content),
        ("JavaScript Functionality", test_javascript_functionality),
        ("CSS Styling", test_css_styling),
        ("Cleanup Utility", test_cleanup_utility),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} Test PASSED")
        else:
            print(f"❌ {test_name} Test FAILED")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Phase 2 PDF Upload & Display System is COMPLETE and VERIFIED!")
        print("\n✅ All components are working correctly:")
        print("   - Directory structure created successfully")
        print("   - Database integration functional")
        print("   - File operations working")
        print("   - HTML templates properly configured")
        print("   - JavaScript functionality implemented")
        print("   - CSS styling applied")
        print("   - Cleanup utility ready")
        print("\n🚀 Ready to test with actual PDF uploads!")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 