"""
__init__.py for routers package
Exports all router instances
"""
from app.presentation.routers.auth import router as auth_router
from app.presentation.routers.categories import router as categories_router
from app.presentation.routers.products import router as products_router
from app.presentation.routers.inventory import router as inventory_router
from app.presentation.routers.carousel import router as carousel_router
from app.presentation.routers.orders import router as orders_router, public_router as orders_public_router
from app.presentation.routers.admin_users import router as admin_users_router
from app.presentation.routers.home_products import router as home_products_router
from app.presentation.routers.ratings import public_router as ratings_public_router, admin_router as ratings_admin_router
from app.presentation.routers.addresses import router as addresses_router

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
