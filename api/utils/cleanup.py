import os
import schedule
import time
from datetime import datetime, timedelta
from api.database.connection import DatabaseManager
from api.database.utils import DatabaseUtils
from api.config.settings import settings

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