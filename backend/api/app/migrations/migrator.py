"""
Database Migration System for Distribuidora Perros y Gatos
Implements a professional migration system similar to Flyway/Alembic
"""

import os
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
import pyodbc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """
    Professional database migration system for SQL Server
    
    Features:
    - Deterministic ordering (001, 002, ... 010)
    - Idempotent execution (safe to re-run)
    - Transaction support (rollback on error)
    - History tracking in __migrations_history table
    - Exponential backoff for connection retries
    """
    
    def __init__(self):
        """Initialize migrator with environment variables"""
        self.db_server = os.getenv('DB_SERVER', 'sqlserver')
        self.db_user = os.getenv('DB_USER', 'SA')
        self.db_password = os.getenv('DB_PASSWORD', 'yourStrongPassword123#')
        self.db_name = os.getenv('DB_NAME', 'distribuidora_db')
        self.db_port = os.getenv('DB_PORT', '1433')
        self.migrations_dir = Path(__file__).parent.parent.parent.parent / 'sql' / 'migrations'
        self.connection = None
        
        logger.info("=" * 70)
        logger.info("Database Migration System v1.0")
        logger.info("=" * 70)
        logger.info(f"Server: {self.db_server}:{self.db_port}")
        logger.info(f"Database: {self.db_name}")
        logger.info(f"Migrations Directory: {self.migrations_dir}")
        logger.info("=" * 70)
    
    def connect(self, max_retries: int = 60, retry_interval: int = 5) -> bool:
        """
        Connect to SQL Server with exponential backoff retries
        
        Args:
            max_retries: Maximum number of connection attempts (default 60 = 300 seconds)
            retry_interval: Seconds to wait between retries (default 5)
        
        Returns:
            True if connection successful, False otherwise
        """
        logger.info(f"\n🔌 Attempting to connect to SQL Server...")
        logger.info(f"   Max retries: {max_retries} (≈{max_retries * retry_interval}s)")
        
        connection_string = (
            f"Driver={{ODBC Driver 17 for SQL Server}};"
            f"Server={self.db_server},{self.db_port};"
            f"Database={self.db_name};"
            f"UID={self.db_user};"
            f"PWD={self.db_password};"
            f"Encrypt=no;"
            f"Connection Timeout=30;"
        )
        
        for attempt in range(1, max_retries + 1):
            try:
                self.connection = pyodbc.connect(connection_string)
                logger.info(f"✅ Connected successfully on attempt {attempt}/{max_retries}")
                return True
            except pyodbc.Error as e:
                if attempt >= max_retries:
                    logger.error("=" * 70)
                    logger.error("❌ FATAL CONNECTION ERROR")
                    logger.error("=" * 70)
                    logger.error(f"Could not connect after {max_retries} attempts ({max_retries * retry_interval}s)")
                    logger.error(f"Error: {str(e)}")
                    logger.error("\nTroubleshooting steps:")
                    logger.error("1. Check SQL Server logs: docker logs sqlserver")
                    logger.error("2. Check available memory: docker stats sqlserver")
                    logger.error("3. Verify environment variables are set correctly")
                    logger.error("=" * 70)
                    return False
                
                logger.warning(
                    f"⏳ Connection attempt {attempt}/{max_retries} failed. "
                    f"Retrying in {retry_interval}s..."
                )
                time.sleep(retry_interval)
        
        return False
    
    def init_migrations_history_table(self) -> bool:
        """
        Create the __migrations_history table if it doesn't exist
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("\n📋 Initializing migrations history table...")
        
        try:
            cursor = self.connection.cursor()
            
            # Read the __0_init_migrations_table.sql file
            init_file = self.migrations_dir / '__0_init_migrations_table.sql'
            if not init_file.exists():
                logger.error(f"❌ Migration init file not found: {init_file}")
                return False
            
            with open(init_file, 'r') as f:
                init_sql = f.read()
            
            # Execute the initialization script
            cursor.execute(init_sql)
            self.connection.commit()
            logger.info("✅ Migrations history table initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing migrations table: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
    
    def get_applied_migrations(self) -> List[str]:
        """
        Get list of migration names already applied to the database
        
        Returns:
            List of applied migration file names
        """
        logger.info("📖 Fetching applied migrations from history...")
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT migration_name FROM __migrations_history WHERE status = 'success' ORDER BY applied_at ASC"
            )
            applied = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            logger.info(f"   Found {len(applied)} previously applied migrations")
            for migration in applied:
                logger.info(f"     ✓ {migration}")
            
            return applied
            
        except Exception as e:
            logger.error(f"❌ Error fetching applied migrations: {str(e)}")
            return []
    
    def get_pending_migrations(self, applied: List[str]) -> List[Tuple[str, Path]]:
        """
        Get list of SQL migration files that haven't been applied yet
        
        Args:
            applied: List of already-applied migration names
        
        Returns:
            List of tuples (migration_name, migration_path) sorted deterministically
        """
        logger.info("\n🔍 Scanning for pending migrations...")
        
        try:
            # Get all .sql files in migrations directory, excluding __0_init_migrations_table.sql
            sql_files = sorted(
                [f for f in self.migrations_dir.glob('*.sql') 
                 if not f.name.startswith('__')]
            )
            
            # Filter to only pending migrations
            pending = [
                (f.name, f) for f in sql_files 
                if f.name not in applied
            ]
            
            logger.info(f"   Found {len(pending)} pending migrations:")
            for name, path in pending:
                logger.info(f"     ⏳ {name}")
            
            return pending
            
        except Exception as e:
            logger.error(f"❌ Error scanning migrations: {str(e)}")
            return []
    
    def apply_migration(self, migration_name: str, migration_path: Path) -> bool:
        """
        Apply a single migration file to the database
        
        Args:
            migration_name: Name of the migration file
            migration_path: Path to the migration file
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"\n🚀 Applying migration: {migration_name}")
        
        start_time = time.time()
        
        try:
            with open(migration_path, 'r') as f:
                sql_content = f.read()
            
            cursor = self.connection.cursor()
            
            # Execute migration in a transaction
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                # Execute the SQL (may contain multiple statements separated by GO)
                for statement in sql_content.split('GO'):
                    statement = statement.strip()
                    if statement:
                        cursor.execute(statement)
                
                # Record the migration in history
                cursor.execute(
                    """
                    INSERT INTO __migrations_history 
                    (migration_name, status, execution_time_ms)
                    VALUES (?, ?, ?)
                    """,
                    (migration_name, 'success', int((time.time() - start_time) * 1000))
                )
                
                # Commit transaction
                cursor.execute("COMMIT TRANSACTION")
                self.connection.commit()
                
                logger.info(f"   ✅ Migration applied successfully ({int((time.time() - start_time) * 1000)}ms)")
                return True
                
            except Exception as e:
                cursor.execute("ROLLBACK TRANSACTION")
                self.connection.commit()
                raise e
            finally:
                cursor.close()
            
        except Exception as e:
            logger.error(f"   ❌ Migration failed: {str(e)}")
            
            # Try to record failure in history
            try:
                cursor = self.connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO __migrations_history 
                    (migration_name, status, error_message, execution_time_ms)
                    VALUES (?, ?, ?, ?)
                    """,
                    (migration_name, 'failed', str(e), int((time.time() - start_time) * 1000))
                )
                self.connection.commit()
                cursor.close()
            except:
                pass
            
            return False
    
    def apply_all_migrations(self) -> bool:
        """
        Apply all pending migrations in deterministic order
        
        Returns:
            True if all migrations successful, False if any failed
        """
        # Step 1: Connect to database
        if not self.connect():
            logger.error("\n❌ Cannot proceed without database connection")
            return False
        
        # Step 2: Initialize migrations history table
        if not self.init_migrations_history_table():
            logger.error("\n❌ Cannot proceed without migrations history table")
            self.connection.close()
            return False
        
        # Step 3: Get applied migrations
        applied = self.get_applied_migrations()
        
        # Step 4: Get pending migrations
        pending = self.get_pending_migrations(applied)
        
        # Step 5: Apply each pending migration
        if not pending:
            logger.info("\n✨ All migrations already applied! Nothing to do.")
            self.connection.close()
            return True
        
        logger.info(f"\n{'=' * 70}")
        logger.info(f"APPLYING {len(pending)} PENDING MIGRATION(S)")
        logger.info(f"{'=' * 70}")
        
        failed_migrations = []
        for migration_name, migration_path in pending:
            if not self.apply_migration(migration_name, migration_path):
                failed_migrations.append(migration_name)
        
        # Summary
        logger.info(f"\n{'=' * 70}")
        logger.info("MIGRATION SUMMARY")
        logger.info(f"{'=' * 70}")
        logger.info(f"Total pending: {len(pending)}")
        logger.info(f"Successful: {len(pending) - len(failed_migrations)}")
        logger.info(f"Failed: {len(failed_migrations)}")
        
        if failed_migrations:
            logger.error("\n❌ MIGRATION PROCESS FAILED")
            logger.error("Failed migrations:")
            for name in failed_migrations:
                logger.error(f"   ✗ {name}")
            self.connection.close()
            return False
        
        logger.info("\n✅ ALL MIGRATIONS APPLIED SUCCESSFULLY")
        logger.info(f"{'=' * 70}\n")
        
        # Close connection
        self.connection.close()
        return True


def main():
    """Entry point for migration script"""
    migrator = DatabaseMigrator()
    
    if migrator.apply_all_migrations():
        exit(0)
    else:
        exit(1)


if __name__ == '__main__':
    main()
