import os
import sqlite3
from contextlib import contextmanager
from typing import Generator
import logging

class DatabaseManager:
    def __init__(self, db_path: str = "./local_database.db"):
        # Support shared in-memory DB for tests
        if db_path == ":memory:shared":
            self.db_path = "file::memory:?cache=shared"
            self.uri = True
        else:
            self.db_path = db_path
            self.uri = False
        if self.db_path not in [":memory:", "file::memory:?cache=shared"]:
            self.setup_database()
    
    def setup_database(self):
        """Initialize database and create tables if they don't exist"""
        with self.get_connection() as conn:
            self.create_tables(conn)
    
    def setup_in_memory_database(self):
        """Setup tables for in-memory database (for testing)"""
        # For in-memory databases, we need to create tables on each connection
        # This method is a no-op for in-memory databases
        pass
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path, uri=getattr(self, 'uri', False), detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        
        # For in-memory databases, create tables on each connection
        if self.db_path in [":memory:", "file::memory:?cache=shared"]:
            self.create_tables(conn)
        
        try:
            yield conn
        finally:
            conn.close()
    
    def create_tables(self, conn: sqlite3.Connection):
        """Create all required database tables"""
        tables = [
            self._create_user_sessions_table(),
            self._create_documents_table(),
            self._create_user_inputs_table(),
            self._create_tax_calculations_table(),
            self._create_ai_conversations_table()
        ]
        
        for table_sql in tables:
            conn.execute(table_sql)
        conn.commit()
    
    def _create_user_sessions_table(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        )
        """
    
    def _create_documents_table(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_url TEXT,
            file_type TEXT NOT NULL,
            upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
        )
        """
    
    def _create_user_inputs_table(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS user_inputs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            input_type TEXT NOT NULL,
            field_name TEXT NOT NULL,
            field_value TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
        )
        """
    
    def _create_tax_calculations_table(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS tax_calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            gross_income REAL,
            tax_old_regime REAL,
            tax_new_regime REAL,
            total_deductions REAL,
            net_tax REAL,
            calculation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
        )
        """
    
    def _create_ai_conversations_table(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS ai_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_message TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
        )
        """ 