from aiogram import Router
from handlers.start   import router as start_router
from handlers.catalog import router as catalog_router
from handlers.cart    import router as cart_router
from handlers.orders  import router as orders_router
from handlers.admin   import router as admin_router

main_router = Router()
main_router.include_routers(
    admin_router,   # admin first — has priority filters
    start_router,
    catalog_router,
    cart_router,
    orders_router,
)
