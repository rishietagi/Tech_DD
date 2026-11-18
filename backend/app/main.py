from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.services.estate.library import validate_all as validate_estate_content
from app.services.intelligence.skills import validate_all as validate_skills
from app.services.report.service import get_report_config


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    # The estate content is practitioner-edited YAML; a malformed edit should stop the
    # server here rather than surface as a broken form on first use.
    validate_estate_content()
    validate_skills()
    get_report_config()

    app = FastAPI(title="Tech DD Platform API", version=settings.api_version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
