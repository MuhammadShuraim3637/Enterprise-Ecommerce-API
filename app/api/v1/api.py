from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.category_router import router as category_router
from app.api.v1.endpoints.product_router import router as product_router
from app.api.v1.endpoints.image import router as image_router
from app.api.v1.endpoints.review_router import router as review_router
from app.api.v1.endpoints.order_router import router as order_router
from app.api.v1.endpoints.payment_router import router as payment_router
from app.api.v1.endpoints.websocket_router import router as websocket_router
from app.api.v1.endpoints.cart_router import router as cart_router


api_router = APIRouter()

# Prefixes ko dhyan se dekh lein:
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(category_router, prefix="/categories", tags=["categories"])
api_router.include_router(product_router, prefix="/products", tags=["products"])
api_router.include_router(image_router, prefix="/products", tags=["product-images"])
api_router.include_router(review_router, prefix="/reviews", tags=["reviews"])
api_router.include_router(order_router, prefix="/orders", tags=["Orders"])
api_router.include_router(payment_router, prefix="/payments", tags=["payments"])
api_router.include_router(websocket_router)
api_router.include_router(cart_router)