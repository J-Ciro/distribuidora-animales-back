"""
Script de inicialización de base de datos
Se ejecuta automáticamente al iniciar el API
"""
import os
import time
import logging
from sqlalchemy import create_engine, text, inspect

logger = logging.getLogger(__name__)

def wait_for_db(engine, max_retries=30, retry_interval=5):
    """Espera a que la base de datos esté disponible"""
    logger.info("Esperando a que SQL Server esté disponible...")
    
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✓ SQL Server está disponible")
            return True
        except Exception as e:
            if attempt >= max_retries:
                logger.error(f"✗ SQL Server no respondió después de {max_retries} intentos")
                logger.error(f"Error: {e}")
                return False
            logger.info(f"SQL Server no está listo (Intento {attempt}/{max_retries}). Esperando {retry_interval} segundos...")
            time.sleep(retry_interval)
    
    return False

def create_database_if_not_exists(db_server, db_user, db_password, db_name):
    """Crea la base de datos si no existe"""
    master_connection_string = f"mssql+pyodbc://{db_user}:{db_password}@{db_server}/master?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&Encrypt=no"
    
    try:
        engine = create_engine(master_connection_string, echo=False)
        
        with engine.connect() as conn:
            # Verificar si la base de datos existe
            result = conn.execute(text(f"SELECT database_id FROM sys.databases WHERE name = '{db_name}'"))
            exists = result.fetchone() is not None
            
            if not exists:
                logger.info(f"Creando base de datos '{db_name}'...")
                conn.execute(text(f"CREATE DATABASE [{db_name}]"))
                conn.commit()
                logger.info(f"✓ Base de datos '{db_name}' creada exitosamente")
            else:
                logger.info(f"✓ Base de datos '{db_name}' ya existe")
        
        engine.dispose()
        return True
    except Exception as e:
        logger.error(f"✗ Error al crear la base de datos: {e}")
        return False

def table_exists(engine, table_name):
    """Verifica si una tabla existe"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def run_sql_file(engine, sql_file_path):
    """Ejecuta un archivo SQL"""
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Dividir por GO statements (SQL Server batch separator)
        batches = [batch.strip() for batch in sql_content.split('GO') if batch.strip()]
        
        with engine.connect() as conn:
            for i, batch in enumerate(batches, 1):
                try:
                    conn.execute(text(batch))
                    conn.commit()
                except Exception as e:
                    # Ignorar errores de objetos que ya existen
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        logger.debug(f"Batch {i}: Objeto ya existe (ignorado)")
                    else:
                        logger.warning(f"Error en batch {i}: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Error al ejecutar archivo SQL {sql_file_path}: {e}")
        return False

def initialize_database():
    """Inicializa la base de datos con el schema y datos iniciales"""
    logger.info("==========================================")
    logger.info("  INICIALIZACIÓN DE BASE DE DATOS")
    logger.info("==========================================")
    
    # Leer variables de entorno
    db_server = os.getenv("DB_SERVER", "localhost")
    db_user = os.getenv("DB_USER", "SA")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME", "distribuidora_db")
    
    if not db_password:
        logger.error("✗ DB_PASSWORD no está configurado")
        return False
    
    # Crear conexión a master para crear la base de datos
    if not create_database_if_not_exists(db_server, db_user, db_password, db_name):
        return False
    
    # Esperar un poco después de crear la BD
    time.sleep(2)
    
    # Conectar a la base de datos específica
    connection_string = f"mssql+pyodbc://{db_user}:{db_password}@{db_server}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&Encrypt=no"
    
    try:
        engine = create_engine(connection_string, echo=False)
        
        # Esperar a que la BD esté lista
        if not wait_for_db(engine, max_retries=10, retry_interval=2):
            logger.error("✗ No se pudo conectar a la base de datos")
            return False
        
        # Verificar si las tablas ya existen
        if table_exists(engine, "Usuarios"):
            logger.info("✓ Las tablas ya existen. Omitiendo inicialización.")
            engine.dispose()
            return True
        
        logger.info("Inicializando schema de base de datos...")
        
        # Buscar archivos SQL
        sql_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "sql")
        schema_file = os.path.join(sql_dir, "schema.sql")
        
        if os.path.exists(schema_file):
            logger.info(f"Aplicando schema desde: {schema_file}")
            if run_sql_file(engine, schema_file):
                logger.info("✓ Schema aplicado exitosamente")
            else:
                logger.warning("⚠ Hubo advertencias al aplicar el schema")
        else:
            logger.warning(f"⚠ No se encontró schema.sql en: {schema_file}")
        
        # Aplicar migraciones si existen
        migrations_dir = os.path.join(sql_dir, "migrations")
        if os.path.exists(migrations_dir) and os.path.isdir(migrations_dir):
            migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])
            for migration_file in migration_files:
                migration_path = os.path.join(migrations_dir, migration_file)
                logger.info(f"Aplicando migración: {migration_file}")
                run_sql_file(engine, migration_path)
        
        # Aplicar seeders si existen
        seeders_dir = os.path.join(sql_dir, "seeders")
        if os.path.exists(seeders_dir) and os.path.isdir(seeders_dir):
            seeder_files = sorted([f for f in os.listdir(seeders_dir) if f.endswith('.sql')])
            for seeder_file in seeder_files:
                seeder_path = os.path.join(seeders_dir, seeder_file)
                logger.info(f"Aplicando seeder: {seeder_file}")
                run_sql_file(engine, seeder_path)
        
        engine.dispose()
        
        logger.info("==========================================")
        logger.info("  ✓ INICIALIZACIÓN COMPLETADA")
        logger.info("==========================================")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error durante la inicialización: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = initialize_database()
    exit(0 if success else 1)
