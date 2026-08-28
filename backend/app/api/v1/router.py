from fastapi import APIRouter

from app.api.v1.routes import engagements, meta, scope

api_router = APIRouter()
api_router.include_router(meta.router)
api_router.include_router(engagements.router)
api_router.include_router(scope.router)
