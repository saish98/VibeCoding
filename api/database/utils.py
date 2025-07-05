import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from .connection import DatabaseManager
from .models import UserSession, Document, UserInput, TaxCalculation, AIConversation

class DatabaseUtils:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_session(self, session_duration_hours: int = 24) -> str:
        """Create a new user session"""
        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(hours=session_duration_hours)
        
        with self.db_manager.get_connection() as conn:
            conn.execute(
                "INSERT INTO user_sessions (session_id, expires_at) VALUES (?, ?)",
                (session_id, expires_at)
            )
            conn.commit()
        
        return session_id
    
    def validate_session(self, session_id: str) -> bool:
        """Check if session exists and is not expired"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT expires_at FROM user_sessions WHERE session_id = ?",
                (session_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                return False
            expires_at_val = result['expires_at']
            if isinstance(expires_at_val, datetime):
                expires_at = expires_at_val
            else:
                expires_at_str = str(expires_at_val)
                try:
                    expires_at = datetime.fromisoformat(expires_at_str)
                except Exception:
                    try:
                        expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S.%f")
                    except Exception:
                        expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S")
            return datetime.now() < expires_at
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions and related data"""
        with self.db_manager.get_connection() as conn:
            # Get expired session IDs
            cursor = conn.execute(
                "SELECT session_id FROM user_sessions WHERE expires_at < ?",
                (datetime.now(),)
            )
            expired_sessions = [row['session_id'] for row in cursor.fetchall()]
            
            if not expired_sessions:
                return 0
            
            # Delete related data
            placeholders = ','.join(['?' for _ in expired_sessions])
            conn.execute(f"DELETE FROM documents WHERE session_id IN ({placeholders})", expired_sessions)
            conn.execute(f"DELETE FROM user_inputs WHERE session_id IN ({placeholders})", expired_sessions)
            conn.execute(f"DELETE FROM tax_calculations WHERE session_id IN ({placeholders})", expired_sessions)
            conn.execute(f"DELETE FROM ai_conversations WHERE session_id IN ({placeholders})", expired_sessions)
            conn.execute(f"DELETE FROM user_sessions WHERE session_id IN ({placeholders})", expired_sessions)
            
            conn.commit()
            return len(expired_sessions)
    
    def get_session_data(self, session_id: str) -> Dict[str, Any]:
        """Get all data associated with a session"""
        if not self.validate_session(session_id):
            return {}
        
        with self.db_manager.get_connection() as conn:
            # Get documents
            documents = conn.execute(
                "SELECT * FROM documents WHERE session_id = ? ORDER BY upload_timestamp DESC",
                (session_id,)
            ).fetchall()
            
            # Get user inputs
            user_inputs = conn.execute(
                "SELECT * FROM user_inputs WHERE session_id = ? ORDER BY timestamp DESC",
                (session_id,)
            ).fetchall()
            
            # Get tax calculations
            tax_calculations = conn.execute(
                "SELECT * FROM tax_calculations WHERE session_id = ? ORDER BY calculation_timestamp DESC",
                (session_id,)
            ).fetchall()
            
            # Get AI conversations
            ai_conversations = conn.execute(
                "SELECT * FROM ai_conversations WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,)
            ).fetchall()
            
            return {
                'documents': [dict(doc) for doc in documents],
                'user_inputs': [dict(input_data) for input_data in user_inputs],
                'tax_calculations': [dict(calc) for calc in tax_calculations],
                'ai_conversations': [dict(conv) for conv in ai_conversations]
            }
    
    def save_document(self, session_id: str, file_name: str, file_url: str, file_type: str) -> int:
        """Save document metadata to database"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO documents (session_id, file_name, file_url, file_type) VALUES (?, ?, ?, ?)",
                (session_id, file_name, file_url, file_type)
            )
            conn.commit()
            return cursor.lastrowid or 0
    
    def save_user_input(self, session_id: str, input_type: str, field_name: str, field_value: str) -> int:
        """Save user input data to database"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO user_inputs (session_id, input_type, field_name, field_value) VALUES (?, ?, ?, ?)",
                (session_id, input_type, field_name, field_value)
            )
            conn.commit()
            return cursor.lastrowid or 0
    
    def save_tax_calculation(self, session_id: str, gross_income: float, tax_old_regime: float, 
                           tax_new_regime: float, total_deductions: float, net_tax: float) -> int:
        """Save tax calculation results to database"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO tax_calculations 
                   (session_id, gross_income, tax_old_regime, tax_new_regime, total_deductions, net_tax) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, gross_income, tax_old_regime, tax_new_regime, total_deductions, net_tax)
            )
            conn.commit()
            return cursor.lastrowid or 0
    
    def save_ai_conversation(self, session_id: str, user_message: str, ai_response: str) -> int:
        """Save AI conversation to database"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO ai_conversations (session_id, user_message, ai_response) VALUES (?, ?, ?)",
                (session_id, user_message, ai_response)
            )
            conn.commit()
            return cursor.lastrowid or 0 