from fastapi import APIRouter

from app.api.v1.routes import (
    assess,
    checklist,
    engagements,
    estate,
    findings,
    irl,
    it_budget,
    meta,
    report,
    research,
    scope,
)

api_router = APIRouter()
api_router.include_router(meta.router)
api_router.include_router(engagements.router)
api_router.include_router(scope.router)
api_router.include_router(research.router)
api_router.include_router(irl.router)
api_router.include_router(checklist.router)
api_router.include_router(assess.router)
api_router.include_router(estate.inventory_router)
api_router.include_router(estate.estate_router)
api_router.include_router(it_budget.router)
api_router.include_router(findings.router)
api_router.include_router(report.router)
