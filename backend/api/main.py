"""
FastAPI main entry point
Distribuidora Perros y Gatos Backend
"""
import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends
from fastapi.routing import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db, close_db, get_db
from app.middleware.error_handler import setup_error_handlers
from app.utils.rabbitmq import rabbitmq_producer

# Configure logging
log_level = logging.INFO if settings.DEBUG else logging.WARNING
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Optional file logging if BACKEND_LOG_FILE or APP_LOG_FILE is set
_log_file = os.getenv("BACKEND_LOG_FILE") or os.getenv("APP_LOG_FILE")
if _log_file:
    try:
        os.makedirs(os.path.dirname(_log_file), exist_ok=True)
        file_handler = logging.FileHandler(_log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        logger.info(f"File logging enabled at {_log_file}")
    except Exception as e:
        logger.warning(f"Could not set up file logging: {e}")
from app.routers.auth import router as auth_router
from app.routers.categories import router as categories_router
from app.routers.products import router as products_router
from app.routers.inventory import router as inventory_router
from app.routers.carousel import router as carousel_router
from app.routers.orders import router as orders_router
from app.routers.public_orders import router as orders_public_router
from app.routers.admin_users import router as admin_users_router
from app.routers.home_products import router as home_products_router
from app.routers.ratings import public_router as ratings_public_router, admin_router as ratings_admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager para startup/shutdown events
    Handles database initialization and cleanup
    """
    # Startup
    print("Starting Distribuidora Perros y Gatos Backend API")
    
    # Inicializar schema de base de datos si es necesario
    try:
        from app.utils.db_init import initialize_database
        print("Inicializando base de datos...")
        initialize_database()
    except Exception as e:
        print(f"Warning: Could not initialize database schema: {str(e)}")
        print("The database may need manual initialization")
    
    # Inicializar conexión de SQLAlchemy
    try:
        init_db()
        print("Database connection pool initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize database connection: {str(e)}")
        print("Application will continue without database connection")
        # Don't raise - allow app to start for development
    
    yield
    
    # Shutdown
    logger.info("Shutting down API")
    try:
        close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {str(e)}")
    
    # Close RabbitMQ connection
    try:
        rabbitmq_producer.close()
        logger.info("RabbitMQ connection closed")
    except Exception as e:
        logger.error(f"Error closing RabbitMQ connection: {str(e)}")


# Crear aplicación FastAPI
app = FastAPI(
    title="Distribuidora Perros y Gatos API",
    description="Backend API para tienda de productos para mascotas",
    version="1.0.0",
    lifespan=lifespan
)

# Determine absolute uploads directory inside the running container or local environment
# Prefer '<base>/uploads' (e.g. '/app/uploads' when WORKDIR=/app), but fall back to '<base>/app/uploads'
BASE_DIR = Path(__file__).resolve().parent  # directory containing main.py (usually '/app')
candidate_a = BASE_DIR / "uploads"
candidate_b = BASE_DIR / "app" / "uploads"

if candidate_a.exists():
    UPLOADS_DIR = candidate_a
elif candidate_b.exists():
    UPLOADS_DIR = candidate_b
else:
    # Create the preferred location (candidate_a)
    UPLOADS_DIR = candidate_a
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Ensure carrusel subfolder exists
(UPLOADS_DIR / "carrusel").mkdir(parents=True, exist_ok=True)

# Synchronize settings.UPLOAD_DIR so other modules use the same absolute path
try:
    settings.UPLOAD_DIR = str(UPLOADS_DIR)
except Exception:
    pass

# Mount static files so requests to /app/uploads/... are served from the uploads folder
app.mount("/app/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para hosts de confianza
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Setup error handlers
setup_error_handlers(app)


# Health check endpoint
@app.get("/health")
def health():
    return {"status": "ok"}

# Minimal admin read-only endpoints for tests
from sqlalchemy.orm import Session
from app.models import Usuario

admin_router = APIRouter(prefix="/api/admin", tags=["admin-utils"])

@admin_router.get("/exists")
def admin_exists(email: str, db: Session = Depends(get_db)):
    try:
        exists = db.query(Usuario).filter(Usuario.email == email, Usuario.es_admin == True).first() is not None
        return {"exists": bool(exists)}
    except Exception as e:
        logger.error(f"Error checking admin exists: {e}")
        return {"exists": False}


@admin_router.get("/count")
def admin_count(db: Session = Depends(get_db)):
    try:
        count = db.query(Usuario).filter(Usuario.es_admin == True).count()
        return {"count": int(count)}
    except Exception as e:
        logger.error(f"Error counting admins: {e}")
        return {"count": 0}





# Importar y incluir routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(categories_router, tags=["categories"])
app.include_router(products_router, tags=["products"])
app.include_router(inventory_router, tags=["inventory"])
app.include_router(carousel_router, tags=["carousel"])
app.include_router(orders_router, tags=["orders"])
app.include_router(orders_public_router, tags=["pedidos-public"])
app.include_router(admin_users_router, tags=["admin-users"])
app.include_router(home_products_router, tags=["home-products"])
app.include_router(ratings_public_router, tags=["ratings"])
app.include_router(ratings_admin_router, tags=["admin-ratings"])

# Test utilities router
app.include_router(admin_router)

# Public routers (frontend)
from app.presentation.routers.carousel import public_router as carousel_public_router
app.include_router(carousel_public_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
