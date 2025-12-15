#!/usr/bin/env python3
"""
Admin User Seeder for Distribuidora Perros y Gatos
Creates a default admin user during application startup if it doesn't exist
"""

import os
import sys
import logging
from datetime import datetime

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyodbc
from passlib.context import CryptContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# Password hashing context (same as in app.utils.security)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


class AdminSeeder:
    """Seeds default admin user into the database"""
    
    def __init__(self):
        """Initialize seeder with environment variables"""
        self.db_server = os.getenv('DB_SERVER', 'sqlserver')
        self.db_user = os.getenv('DB_USER', 'SA')
        self.db_password = os.getenv('DB_PASSWORD', 'yourStrongPassword123#')
        self.db_name = os.getenv('DB_NAME', 'distribuidora_db')
        self.db_port = os.getenv('DB_PORT', '1433')
        
        # Admin credentials from environment
        self.admin_email = os.getenv('ADMIN_EMAIL', 'admin@gmail.com')
        self.admin_password = os.getenv('ADMIN_PASSWORD', 'Admin123!@#')
        
        self.connection = None
        
        logger.info("=" * 70)
        logger.info("Admin User Seeder v1.0")
        logger.info("=" * 70)
        logger.info(f"Admin Email: {self.admin_email}")
        logger.info("=" * 70)
    
    def connect(self) -> bool:
        """Connect to SQL Server"""
        logger.info("\n🔌 Connecting to database...")
        
        connection_string = (
            f"Driver={{ODBC Driver 17 for SQL Server}};"
            f"Server={self.db_server},{self.db_port};"
            f"Database={self.db_name};"
            f"UID={self.db_user};"
            f"PWD={self.db_password};"
            f"Encrypt=no;"
            f"Connection Timeout=30;"
        )
        
        try:
            self.connection = pyodbc.connect(connection_string)
            logger.info("✅ Connected successfully")
            return True
        except pyodbc.Error as e:
            logger.error(f"❌ Connection failed: {str(e)}")
            return False
    
    def admin_exists(self) -> bool:
        """Check if admin user already exists"""
        logger.info("\n📋 Checking if admin user exists...")
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT id FROM Usuarios WHERE email = ? AND es_admin = 1",
                (self.admin_email,)
            )
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                logger.info(f"✅ Admin user already exists (ID: {result[0]})")
                return True
            else:
                logger.info("❌ Admin user does not exist")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error checking admin existence: {str(e)}")
            return True  # Assume exists to be safe
    
    def create_admin(self) -> bool:
        """Create the default admin user"""
        logger.info("\n👤 Creating admin user...")
        
        try:
            # Hash the password
            password_hash = pwd_context.hash(self.admin_password)
            
            cursor = self.connection.cursor()
            
            # Insert admin user
            # Note: nombre_completo is required, setting to "Administrator"
            cursor.execute(
                """
                INSERT INTO Usuarios 
                (nombre_completo, email, cedula, password_hash, es_admin, is_active, fecha_registro, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    'Administrator',  # nombre_completo
                    self.admin_email,  # email
                    '0000000000',      # cedula (placeholder for admin)
                    password_hash,     # password_hash (bcrypt hashed)
                    True,              # es_admin = 1
                    True,              # is_active = 1 (admin automatically verified)
                    datetime.utcnow(),  # fecha_registro
                    datetime.utcnow(),  # created_at
                    datetime.utcnow()   # updated_at
                )
            )
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ Admin user created successfully")
            logger.info(f"   Email: {self.admin_email}")
            logger.info(f"   Role: Administrator")
            logger.info(f"   Status: Active (verified)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating admin user: {str(e)}")
            self.connection.rollback()
            return False
    
    def seed(self) -> bool:
        """Execute seeding process"""
        # Connect to database
        if not self.connect():
            return False
        
        # Check if admin already exists
        if self.admin_exists():
            logger.info("\n✨ Admin seeding skipped (already exists)")
            self.connection.close()
            return True
        
        # Create admin user
        if not self.create_admin():
            logger.error("\n❌ ADMIN SEEDING FAILED")
            self.connection.close()
            return False
        
        logger.info("\n✅ ADMIN SEEDING COMPLETED SUCCESSFULLY")
        logger.info("=" * 70 + "\n")
        
        # Close connection
        self.connection.close()
        return True


def main():
    """Entry point for admin seeder"""
    seeder = AdminSeeder()
    
    if seeder.seed():
        exit(0)
    else:
        exit(1)


if __name__ == '__main__':
    main()
