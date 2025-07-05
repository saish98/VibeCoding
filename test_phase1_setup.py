#!/usr/bin/env python3
"""
Phase 1 Database Setup Verification Script
Tests all components of the database setup as specified in Phase1_Database_Setup.md
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
import tempfile

# Add the api directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

# Load environment variables
load_dotenv('.env.local')

from database.connection import DatabaseManager
from database.utils import DatabaseUtils
from database.migrations import DatabaseMigration
from config.settings import settings

def test_database_connection():
    """Test 1.1: Database Connection Test"""
    print("🔍 Testing Database Connection...")
    
    try:
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db_manager = DatabaseManager(tmp.name)
            utils = DatabaseUtils(db_manager)
            session_id = utils.create_session()
            print(f"✓ Session created: {session_id[:8]}...")
            valid = utils.validate_session(session_id)
            if valid:
                print("✓ Session validation successful")
            else:
                print("✗ Session validation failed")
                return False
            expired_count = utils.cleanup_expired_sessions()
            print(f"✓ Cleaned up {expired_count} expired sessions")
        return True
    except Exception as e:
        print(f"✗ Database connection test failed: {e}")
        return False

def test_database_schema():
    """Test 1.2: Schema Validation Test"""
    print("\n🔍 Testing Database Schema...")
    
    try:
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db_manager = DatabaseManager(tmp.name)
            with db_manager.get_connection() as conn:
                tables = ['user_sessions', 'documents', 'user_inputs', 'tax_calculations', 'ai_conversations']
                for table in tables:
                    cursor = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                    result = cursor.fetchone()
                    if result:
                        print(f"✓ Table {table} exists")
                    else:
                        print(f"✗ Table {table} does not exist")
                        return False
        return True
    except Exception as e:
        print(f"✗ Schema validation test failed: {e}")
        return False

def test_database_operations():
    """Test 1.3: Database Operations Test"""
    print("\n🔍 Testing Database Operations...")
    
    try:
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db_manager = DatabaseManager(tmp.name)
            utils = DatabaseUtils(db_manager)
            session_id = utils.create_session()
            doc_id = utils.save_document(session_id, "test.pdf", "/uploads/test.pdf", "pay_slip")
            print(f"✓ Document saved with ID: {doc_id}")
            input_id = utils.save_user_input(session_id, "salary", "basic_salary", "500000")
            print(f"✓ User input saved with ID: {input_id}")
            calc_id = utils.save_tax_calculation(session_id, 500000.0, 50000.0, 45000.0, 100000.0, 40000.0, "Test Employee")
            print(f"✓ Tax calculation saved with ID: {calc_id}")
            conv_id = utils.save_ai_conversation(session_id, "What is my tax liability?", "Based on your income...")
            print(f"✓ AI conversation saved with ID: {conv_id}")
            session_data = utils.get_session_data(session_id)
            docs = session_data.get('documents', [])
            user_inputs = session_data.get('user_inputs', [])
            tax_calcs = session_data.get('tax_calculations', [])
            ai_convs = session_data.get('ai_conversations', [])
            assert len(docs) == 1, f"Expected 1 document, got {len(docs)}"
            assert len(user_inputs) == 1, f"Expected 1 user input, got {len(user_inputs)}"
            assert len(tax_calcs) == 1, f"Expected 1 tax calculation, got {len(tax_calcs)}"
            assert len(ai_convs) == 1, f"Expected 1 AI conversation, got {len(ai_convs)}"
            print("✓ Session data retrieval successful")
        return True
    except Exception as e:
        print(f"✗ Database operations test failed: {e}")
        return False

def test_migration_system():
    """Test 1.4: Migration System Test"""
    print("\n🔍 Testing Migration System...")
    
    try:
        # Test with a temporary database file
        test_db_path = "./test_migration_phase1.db"
        
        # Remove test database if it exists
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        migration = DatabaseMigration(test_db_path)
        migration.run_migrations()
        
        # Verify migrations were applied
        applied_migrations = migration.get_applied_migrations()
        assert "001_initial_schema" in applied_migrations
        print("✓ Migration system test successful")
        
        # Clean up
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        return True
    except Exception as e:
        print(f"✗ Migration system test failed: {e}")
        return False

def test_environment_configuration():
    """Test 1.5: Environment Configuration Test"""
    print("\n🔍 Testing Environment Configuration...")
    
    try:
        # Validate settings
        settings.validate()
        
        # Check required settings
        assert settings.DATABASE_TYPE == "sqlite"
        assert settings.DEBUG == True
        assert settings.SESSION_TIMEOUT_HOURS == 24
        assert settings.MAX_FILE_SIZE == 10485760
        assert settings.UPLOAD_FOLDER == "./uploads"
        
        print("✓ Environment configuration test successful")
        return True
    except Exception as e:
        print(f"✗ Environment configuration test failed: {e}")
        return False

def test_file_structure():
    """Test 1.6: File Structure Verification"""
    print("\n🔍 Testing File Structure...")
    
    required_files = [
        "api/__init__.py",
        "api/main.py",
        "api/database/__init__.py",
        "api/database/connection.py",
        "api/database/models.py",
        "api/database/utils.py",
        "api/database/migrations.py",
        "api/config/__init__.py",
        "api/config/settings.py",
        "requirements.txt",
        ".env.local"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✓ {file_path} exists")
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    
    print("✓ All required files exist")
    return True

def main():
    """Run all Phase 1 tests"""
    print("🚀 Phase 1 Database Setup Verification")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Environment Configuration", test_environment_configuration),
        ("Database Connection", test_database_connection),
        ("Database Schema", test_database_schema),
        ("Database Operations", test_database_operations),
        ("Migration System", test_migration_system),
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
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Phase 1 Database Setup is COMPLETE and VERIFIED!")
        print("\n✅ All components are working correctly:")
        print("   - Database schema created successfully")
        print("   - Connection management working")
        print("   - Session management functional")
        print("   - Migration system operational")
        print("   - Environment configuration loaded")
        print("   - File structure verified")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 