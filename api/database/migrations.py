import os
import sqlite3
from typing import List, Tuple
from datetime import datetime

class DatabaseMigration:
    def __init__(self, db_path: str = "./local_database.db"):
        self.db_path = db_path
        self.migrations_table = "schema_migrations"
        self.setup_migrations_table()
    
    def setup_migrations_table(self):
        """Create migrations tracking table"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_name TEXT UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migrations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"SELECT migration_name FROM {self.migrations_table}")
            return [row[0] for row in cursor.fetchall()]
    
    def apply_migration(self, migration_name: str, sql_commands: List[str]):
        """Apply a migration"""
        with sqlite3.connect(self.db_path) as conn:
            try:
                for sql in sql_commands:
                    conn.execute(sql)
                
                conn.execute(
                    f"INSERT INTO {self.migrations_table} (migration_name) VALUES (?)",
                    (migration_name,)
                )
                conn.commit()
                print(f"✓ Applied migration: {migration_name}")
            except Exception as e:
                conn.rollback()
                print(f"✗ Failed to apply migration {migration_name}: {e}")
                raise
    
    def run_migrations(self):
        """Run all pending migrations"""
        applied = self.get_applied_migrations()
        
        # Define migrations
        migrations = [
            ("001_initial_schema", [
                """CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )""",
                """CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_url TEXT,
                    file_type TEXT NOT NULL,
                    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
                )""",
                """CREATE TABLE IF NOT EXISTS user_inputs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    input_type TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    field_value TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
                )""",
                """CREATE TABLE IF NOT EXISTS tax_calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    gross_income REAL,
                    tax_old_regime REAL,
                    tax_new_regime REAL,
                    total_deductions REAL,
                    net_tax REAL,
                    calculation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
                )""",
                """CREATE TABLE IF NOT EXISTS ai_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
                )"""
            ])
        ]
        
        for migration_name, sql_commands in migrations:
            if migration_name not in applied:
                self.apply_migration(migration_name, sql_commands) 