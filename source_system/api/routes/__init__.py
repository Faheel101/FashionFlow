"""API route modules for the FashionFlow Commerce API."""

from source_system.api.routes.customers import router as customers_router
from source_system.api.routes.order_items import router as order_items_router
from source_system.api.routes.orders import router as orders_router
from source_system.api.routes.payments import router as payments_router
from source_system.api.routes.products import router as products_router
from source_system.api.routes.refunds import router as refunds_router

ALL_ROUTERS = [
    customers_router,
    products_router,
    orders_router,
    order_items_router,
    payments_router,
    refunds_router,
]

__all__ = ["ALL_ROUTERS"]
