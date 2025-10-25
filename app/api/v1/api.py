from fastapi import APIRouter
from app.api.v1 import auth, contacts, calls, webhooks, activities, websocket, security, monitoring, admin

api_router = APIRouter()

# Include all routers (they have their own prefixes and tags)
api_router.include_router(auth.router)
api_router.include_router(contacts.router)
api_router.include_router(calls.router)
api_router.include_router(activities.router)
api_router.include_router(websocket.router)
api_router.include_router(security.router)
api_router.include_router(monitoring.router)
api_router.include_router(webhooks.router)
api_router.include_router(admin.router)