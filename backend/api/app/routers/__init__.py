"""
__init__.py for routers package
Exports all router instances
"""
from app.routers.auth import router as auth_router
from app.routers.categories import router as categories_router
from app.routers.products import router as products_router
from app.routers.inventory import router as inventory_router
from app.routers.carousel import router as carousel_router
from app.routers.orders import router as orders_router, public_router as orders_public_router
from app.routers.admin_users import router as admin_users_router
from app.routers.home_products import router as home_products_router
from app.routers.ratings import public_router as ratings_public_router, admin_router as ratings_admin_router
from app.routers.addresses import router as addresses_router

__all__ = [
    'auth_router',
    'categories_router',
    'products_router',
    'inventory_router',
    'carousel_router',
    'orders_router',
    'orders_public_router',
    'admin_users_router',
    'home_products_router',
    'ratings_public_router',
    'ratings_admin_router',
    'addresses_router',
]
