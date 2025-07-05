#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from database.connection import DatabaseManager
import sqlite3

print("Testing database connection...")

# Test 1: In-memory database
print("\n1. Testing in-memory database:")
db_manager = DatabaseManager(":memory:")
db_manager.setup_in_memory_database()

with db_manager.get_connection() as conn:
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables in memory DB: {tables}")

# Test 2: File database
print("\n2. Testing file database:")
db_manager2 = DatabaseManager("./test_debug.db")

with db_manager2.get_connection() as conn:
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables in file DB: {tables}")

# Clean up
if os.path.exists("./test_debug.db"):
    os.remove("./test_debug.db") 