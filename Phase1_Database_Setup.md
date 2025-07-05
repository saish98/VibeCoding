# Phase 1: Database Setup & Connection (SQLite + Hybrid Database Module)

## Overview
Phase 1 focuses on establishing the foundational database layer for the Tax Advisor application. This phase implements a hybrid database approach that supports both local SQLite development and production PostgreSQL deployment, ensuring seamless transition between development and production environments.

## Objectives
- [ ] Set up SQLite database for local development
- [ ] Create hybrid database module for environment-based database selection
- [ ] Implement database schema with all required tables
- [ ] Establish database connection management
- [ ] Create database initialization scripts
- [ ] Set up environment variable configuration
- [ ] Implement database migration utilities

## Database Schema Design

### Core Tables Structure

#### 1. user_sessions
```sql
CREATE TABLE user_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);
```
**Purpose:** Manages user session data for temporary access control
**Key Features:**
- Unique session identifiers for secure access
- Automatic expiration handling
- GDPR-compliant temporary storage

#### 2. documents
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(255) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_url TEXT,
    file_type VARCHAR(50) NOT NULL,
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
);
```
**Purpose:** Stores uploaded PDF document metadata
**Key Features:**
- Links documents to user sessions
- Supports both Pay Slip and Form 16 file types
- Tracks upload timestamps for cleanup

#### 3. user_inputs
```sql
CREATE TABLE user_inputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(255) NOT NULL,
    input_type VARCHAR(100) NOT NULL,
    field_name VARCHAR(255) NOT NULL,
    field_value TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
);
```
**Purpose:** Stores manual data input from users
**Key Features:**
- Flexible schema for various input types
- Session-based data organization
- Audit trail with timestamps

#### 4. tax_calculations
```sql
CREATE TABLE tax_calculations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(255) NOT NULL,
    gross_income DECIMAL(15,2),
    tax_old_regime DECIMAL(15,2),
    tax_new_regime DECIMAL(15,2),
    total_deductions DECIMAL(15,2),
    net_tax DECIMAL(15,2),
    calculation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
);
```
**Purpose:** Stores calculated tax results
**Key Features:**
- Dual regime comparison storage
- Precise decimal calculations
- Historical calculation tracking

#### 5. ai_conversations
```sql
CREATE TABLE ai_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(255) NOT NULL,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
);
```
**Purpose:** Stores AI chat conversation history
**Key Features:**
- Complete conversation tracking
- Context preservation for AI responses
- Session-based conversation isolation

## Implementation Tasks

### Task 1.1: Project Structure Setup
```
tax-advisor/
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── models.py
│   │   ├── migrations.py
│   │   └── utils.py
│   └── config/
│       ├── __init__.py
│       └── settings.py
├── local_database.db
├── requirements.txt
├── .env.local
└── README.md
```

### Task 1.2: Environment Configuration
Create `.env.local` file:
```env
# Database Configuration
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./local_database.db

# Application Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
SESSION_TIMEOUT_HOURS=24

# File Storage (Local Development)
UPLOAD_FOLDER=./uploads
MAX_FILE_SIZE=10485760  # 10MB

# Gemini API (for later phases)
GEMINI_API_KEY=your-gemini-api-key
```

### Task 1.3: Database Connection Module
**File: `api/database/connection.py`**
```python
import os
import sqlite3
from contextlib import contextmanager
from typing import Generator
import logging

class DatabaseManager:
    def __init__(self, db_path: str = "./local_database.db"):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Initialize database and create tables if they don't exist"""
        with self.get_connection() as conn:
            self.create_tables(conn)
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
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
```

### Task 1.4: Database Models
**File: `api/database/models.py`**
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

@dataclass
class UserSession:
    session_id: str
    created_at: datetime
    expires_at: datetime

@dataclass
class Document:
    id: Optional[int]
    session_id: str
    file_name: str
    file_url: Optional[str]
    file_type: str
    upload_timestamp: datetime

@dataclass
class UserInput:
    id: Optional[int]
    session_id: str
    input_type: str
    field_name: str
    field_value: Optional[str]
    timestamp: datetime

@dataclass
class TaxCalculation:
    id: Optional[int]
    session_id: str
    gross_income: Optional[Decimal]
    tax_old_regime: Optional[Decimal]
    tax_new_regime: Optional[Decimal]
    total_deductions: Optional[Decimal]
    net_tax: Optional[Decimal]
    calculation_timestamp: datetime

@dataclass
class AIConversation:
    id: Optional[int]
    session_id: str
    user_message: str
    ai_response: str
    timestamp: datetime
```

### Task 1.5: Database Utilities
**File: `api/database/utils.py`**
```python
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
            
            expires_at = datetime.fromisoformat(result['expires_at'])
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
```

### Task 1.6: Database Migration System
**File: `api/database/migrations.py`**
```python
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
```

### Task 1.7: Configuration Management
**File: `api/config/settings.py`**
```python
import os
from typing import Optional

class Settings:
    # Database Configuration
    DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "sqlite")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./local_database.db")
    
    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SESSION_TIMEOUT_HOURS: int = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
    
    # File Storage
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "./uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    
    # API Keys (for later phases)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    @classmethod
    def validate(cls):
        """Validate required settings"""
        if not cls.SECRET_KEY or cls.SECRET_KEY == "dev-secret-key-change-in-production":
            print("⚠️  Warning: Using default secret key. Change in production!")
        
        if not os.path.exists(cls.UPLOAD_FOLDER):
            os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
            print(f"✓ Created upload folder: {cls.UPLOAD_FOLDER}")

# Global settings instance
settings = Settings()
```

## Testing & Validation

### Test 1.1: Database Connection Test
```python
# test_database.py
import pytest
from api.database.connection import DatabaseManager
from api.database.utils import DatabaseUtils

def test_database_connection():
    db_manager = DatabaseManager(":memory:")  # Use in-memory for testing
    utils = DatabaseUtils(db_manager)
    
    # Test session creation
    session_id = utils.create_session()
    assert session_id is not None
    
    # Test session validation
    assert utils.validate_session(session_id) == True
    
    # Test session cleanup
    expired_count = utils.cleanup_expired_sessions()
    assert expired_count >= 0
```

### Test 1.2: Schema Validation Test
```python
def test_database_schema():
    db_manager = DatabaseManager(":memory:")
    
    with db_manager.get_connection() as conn:
        # Check if all tables exist
        tables = ['user_sessions', 'documents', 'user_inputs', 'tax_calculations', 'ai_conversations']
        
        for table in tables:
            cursor = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            assert cursor.fetchone() is not None, f"Table {table} does not exist"
```

## Deliverables Checklist

- [ ] **Database Schema**: All 5 tables created with proper relationships
- [ ] **Connection Module**: SQLite connection management with context managers
- [ ] **Models**: Data classes for all database entities
- [ ] **Utilities**: Session management, data retrieval, and cleanup functions
- [ ] **Migration System**: Database versioning and schema updates
- [ ] **Configuration**: Environment-based settings management
- [ ] **Testing**: Unit tests for database operations
- [ ] **Documentation**: Code comments and usage examples

## Success Criteria

1. **Database Initialization**: SQLite database can be created and initialized automatically
2. **Session Management**: User sessions can be created, validated, and cleaned up
3. **Data Operations**: All CRUD operations work correctly for each table
4. **Migration System**: Database schema can be updated safely
5. **Environment Configuration**: Settings load correctly from environment variables
6. **Error Handling**: Graceful handling of database errors and edge cases

## Next Phase Preparation

Phase 1 completion enables:
- **Phase 2**: PDF upload system can store document metadata
- **Phase 3**: User input forms can persist data to database
- **Phase 4**: Tax calculations can be stored and retrieved
- **Phase 5**: AI conversations can be logged and retrieved
- **Phase 6**: Chat system can maintain conversation context
- **Phase 7**: Complete application can function with persistent data

## Estimated Timeline
- **Database Schema Design**: 2 hours
- **Connection Module**: 3 hours
- **Models & Utilities**: 4 hours
- **Migration System**: 2 hours
- **Configuration**: 1 hour
- **Testing**: 3 hours
- **Documentation**: 1 hour

**Total Estimated Time: 16 hours**

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|-------------------|
| Schema changes during development | Migration system allows safe schema updates |
| Database corruption | Regular backups and validation checks |
| Performance issues | Index optimization and query tuning |
| Data loss | Transaction management and rollback capabilities |
| Environment conflicts | Clear separation of dev/prod configurations |

---

**Phase 1 Goal**: Working local database with complete schema, connection management, and utilities for the Tax Advisor application. 