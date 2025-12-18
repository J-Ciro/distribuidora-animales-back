#!/usr/bin/env python3
"""
Execute SQL migration against SQL Server using SQLAlchemy
This script connects to SQL Server and applies a migration
"""

import sys
import os
from pathlib import Path

# Add backend API to path
sys.path.insert(0, str(Path(__file__).parent / "backend" / "api"))

from sqlalchemy import text, create_engine
from app.config import settings

MIGRATION_FILE = r"c:\Users\juan.ciro\Documents\Taller-11\distribuidora-animales-back\sql\migrations\011_add_missing_usuario_columns.sql"

def execute_migration():
    """Execute the migration file"""
    try:
        print("=" * 50)
        print("SQL Server Migration Executor (SQLAlchemy)")
        print("=" * 50)
        print(f"Database URL: {settings.DATABASE_URL}")
        print(f"Migration: {os.path.basename(MIGRATION_FILE)}")
        print("=" * 50)
        
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Read migration file
        with open(MIGRATION_FILE, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print("Migration file loaded successfully")
        print("=" * 50)
        print("Executing migration...")
        print("=" * 50)
        
        # Split by GO statements and execute each batch
        batches = sql_script.split('GO')
        
        with engine.connect() as connection:
            for i, batch in enumerate(batches):
                batch = batch.strip()
                if batch:
                    print(f"\nBatch {i + 1}:")
                    try:
                        connection.execute(text(batch))
                        connection.commit()
                        print(f"  Executed successfully")
                    except Exception as e:
                        print(f"  Error: {e}")
                        connection.rollback()
                        return False
        
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = execute_migration()
    sys.exit(0 if success else 1)
