#!/usr/bin/env python3
"""
Test script for Phase 1 Database Setup
Validates all database components are working correctly
"""

import sys
import os
from datetime import datetime, timedelta

# Add the api directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from api.database.connection import DatabaseManager
from api.database.utils import DatabaseUtils
from api.database.migrations import DatabaseMigration
from api.config.settings import settings

def test_database_connection():
    """Test database connection and table creation"""
    print("🧪 Testing database connection...")
    
    try:
        # Test with a temporary database file
        test_db_path = "./test_database.db"
        db_manager = DatabaseManager(test_db_path)
        print("✓ Database manager created successfully")
        
        # Test connection
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
        print("✓ Database connection working")
        
        # Test if tables were created
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✓ Tables created: {tables}")
        
        return db_manager
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return None

def test_database_utils(db_manager):
    """Test database utilities"""
    print("\n🧪 Testing database utilities...")
    
    try:
        utils = DatabaseUtils(db_manager)
        print("✓ Database utils created successfully")
        
        # Test session creation
        session_id = utils.create_session()
        assert session_id is not None
        print(f"✓ Session created: {session_id[:8]}...")
        
        # Test session validation
        assert utils.validate_session(session_id) == True
        print("✓ Session validation working")
        
        # Test session data retrieval
        session_data = utils.get_session_data(session_id)
        assert isinstance(session_data, dict)
        print("✓ Session data retrieval working")
        
        # Test cleanup (should return 0 for new sessions)
        expired_count = utils.cleanup_expired_sessions()
        assert expired_count >= 0
        print(f"✓ Session cleanup working (expired: {expired_count})")
        
        return utils, session_id
    except Exception as e:
        print(f"✗ Database utils test failed: {e}")
        return None, None

def test_database_operations(utils, session_id):
    """Test CRUD operations"""
    print("\n🧪 Testing database operations...")
    
    try:
        # Test document save
        doc_id = utils.save_document(
            session_id=session_id,
            file_name="test_payslip.pdf",
            file_url="/uploads/test_payslip.pdf",
            file_type="payslip"
        )
        assert doc_id > 0
        print(f"✓ Document saved with ID: {doc_id}")
        
        # Test user input save
        input_id = utils.save_user_input(
            session_id=session_id,
            input_type="salary",
            field_name="basic_salary",
            field_value="500000"
        )
        assert input_id > 0
        print(f"✓ User input saved with ID: {input_id}")
        
        # Test tax calculation save
        calc_id = utils.save_tax_calculation(
            session_id=session_id,
            gross_income=500000.0,
            tax_old_regime=25000.0,
            tax_new_regime=30000.0,
            total_deductions=50000.0,
            net_tax=25000.0
        )
        assert calc_id > 0
        print(f"✓ Tax calculation saved with ID: {calc_id}")
        
        # Test AI conversation save
        conv_id = utils.save_ai_conversation(
            session_id=session_id,
            user_message="What is my tax liability?",
            ai_response="Based on your income, your tax liability is ₹25,000 under the old regime."
        )
        assert conv_id > 0
        print(f"✓ AI conversation saved with ID: {conv_id}")
        
        # Test data retrieval
        session_data = utils.get_session_data(session_id)
        assert len(session_data['documents']) == 1
        assert len(session_data['user_inputs']) == 1
        assert len(session_data['tax_calculations']) == 1
        assert len(session_data['ai_conversations']) == 1
        print("✓ All data retrieved successfully")
        
        return True
    except Exception as e:
        print(f"✗ Database operations test failed: {e}")
        return False

def test_migration_system():
    """Test migration system"""
    print("\n🧪 Testing migration system...")
    
    try:
        # Test with a temporary database file
        test_db_path = "./test_migration.db"
        migration = DatabaseMigration(test_db_path)
        print("✓ Migration system created")
        
        # Run migrations
        migration.run_migrations()
        print("✓ Migrations applied successfully")
        
        # Check applied migrations
        applied = migration.get_applied_migrations()
        assert "001_initial_schema" in applied
        print(f"✓ Migration tracking working: {applied}")
        
        return True
    except Exception as e:
        print(f"✗ Migration system test failed: {e}")
        return False

def test_configuration():
    """Test configuration management"""
    print("\n🧪 Testing configuration...")
    
    try:
        # Validate settings
        settings.validate()
        print("✓ Configuration validated")
        
        # Check key settings
        assert settings.DATABASE_TYPE == "sqlite"
        assert settings.DEBUG == True
        assert settings.SESSION_TIMEOUT_HOURS == 24
        print("✓ Settings loaded correctly")
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Phase 1 Database Setup Tests\n")
    
    # Test database connection
    db_manager = test_database_connection()
    if not db_manager:
        print("\n❌ Database connection test failed. Exiting.")
        return False
    
    # Test database utilities
    utils, session_id = test_database_utils(db_manager)
    if not utils:
        print("\n❌ Database utilities test failed. Exiting.")
        return False
    
    # Test database operations
    operations_ok = test_database_operations(utils, session_id)
    if not operations_ok:
        print("\n❌ Database operations test failed.")
        return False
    
    # Test migration system
    migration_ok = test_migration_system()
    if not migration_ok:
        print("\n❌ Migration system test failed.")
        return False
    
    # Test configuration
    config_ok = test_configuration()
    if not config_ok:
        print("\n❌ Configuration test failed.")
        return False
    
    print("\n🎉 All Phase 1 tests passed successfully!")
    print("\n✅ Database Setup Complete:")
    print("   - SQLite database connection working")
    print("   - All tables created successfully")
    print("   - Session management functional")
    print("   - CRUD operations working")
    print("   - Migration system operational")
    print("   - Configuration management working")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 