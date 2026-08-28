from fastapi import APIRouter

from app.core.config import get_settings
from app.reference.seed_enums import build_enums_payload
from app.schemas.meta import EnumsResponse

router = APIRouter(tags=["meta"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": get_settings().api_version}


@router.get("/meta/enums", response_model=EnumsResponse)
def get_enums() -> EnumsResponse:
    return EnumsResponse(enums=build_enums_payload())
