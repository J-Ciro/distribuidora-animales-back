#!/usr/bin/env python3
"""
Execute SQL migration against SQL Server
This script connects to SQL Server and applies a migration file
"""

import pyodbc
import os
import sys

# Connection parameters
SERVER = "localhost"
PORT = 1433
USERNAME = "sa"
PASSWORD = "YourStrongPassword123!"
DATABASE = "distribuidora_db"
MIGRATION_FILE = r"c:\Users\juan.ciro\Documents\Taller-11\distribuidora-animales-back\sql\migrations\011_add_missing_usuario_columns.sql"

def get_connection():
    """Create and return a database connection"""
    try:
        connection_string = f"Driver={{ODBC Driver 17 for SQL Server}};Server=tcp:{SERVER},{PORT};Database={DATABASE};Uid={USERNAME};Pwd={PASSWORD};Encrypt=yes;Connection Timeout=30;TrustServerCertificate=yes"
        conn = pyodbc.connect(connection_string, autocommit=False)
        return conn
    except pyodbc.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def execute_migration(conn, migration_file):
    """Execute the migration file"""
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print(f"Migration file loaded: {migration_file}")
        print("=" * 50)
        print("Executing migration...")
        print("=" * 50)
        
        cursor = conn.cursor()
        
        # Split by GO statements and execute each batch
        batches = sql_script.split('GO')
        for i, batch in enumerate(batches):
            batch = batch.strip()
            if batch:
                print(f"\nBatch {i + 1}:")
                try:
                    cursor.execute(batch)
                    print(f"  Executed successfully")
                except pyodbc.Error as e:
                    print(f"  Error: {e}")
                    conn.rollback()
                    return False
        
        conn.commit()
        cursor.close()
        return True
        
    except Exception as e:
        print(f"Error executing migration: {e}")
        return False

def main():
    print("=" * 50)
    print("SQL Server Migration Executor")
    print("=" * 50)
    print(f"Server: {SERVER}:{PORT}")
    print(f"Database: {DATABASE}")
    print(f"Migration: {os.path.basename(MIGRATION_FILE)}")
    print("=" * 50)
    
    conn = get_connection()
    print("Connected to database successfully!")
    
    success = execute_migration(conn, MIGRATION_FILE)
    conn.close()
    
    if success:
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        print("=" * 50)
        sys.exit(0)
    else:
        print("\n" + "=" * 50)
        print("Migration failed!")
        print("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()
