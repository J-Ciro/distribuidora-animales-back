import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_SERVER = os.environ.get('DB_SERVER', 'sqlserver')
DB_PORT = os.environ.get('DB_PORT', '1433')
DB_NAME = os.environ.get('DB_NAME', 'distribuidora_db')
DB_USER = os.environ.get('DB_USER', 'SA')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'yourStrongPassword123#')

# Usamos pyodbc driver
DRIVER = os.environ.get('ODBC_DRIVER', 'ODBC Driver 18 for SQL Server')

CONN_STR = f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}:{DB_PORT}/{DB_NAME}?driver={DRIVER.replace(' ', '+')}"

engine = create_engine(CONN_STR, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
