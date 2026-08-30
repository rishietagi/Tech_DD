from fastapi import APIRouter

from app.core.config import get_settings
from app.reference.seed_enums import build_enums_payload
from app.schemas.meta import EnumsResponse
from app.schemas.scope_api import LibraryRowSummary, WorkstreamLibraryResponse
from app.services.scope.library import get_scope_library

router = APIRouter(tags=["meta"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": get_settings().api_version}


@router.get("/meta/enums", response_model=EnumsResponse)
def get_enums() -> EnumsResponse:
    return EnumsResponse(enums=build_enums_payload())


@router.get("/meta/workstreams", response_model=WorkstreamLibraryResponse)
def get_workstream_library() -> WorkstreamLibraryResponse:
    """The KPMG scope library.

    The methodology page renders from this rather than duplicating the prose, so the
    documentation and the engine can never drift apart.
    """
    library = get_scope_library()
    return WorkstreamLibraryResponse(
        library_version=library.manifest.library_version,
        source_document=library.manifest.source_document,
        source_owner=library.manifest.source_owner,
        decks={
            deck_id: [
                LibraryRowSummary(
                    id=row.id,
                    sn=row.sn,
                    deck=deck_id,
                    title=row.title,
                    lines=row.body_lines,
                    workstreams=row.workstreams,
                    base_tier=row.base_tier,
                    always_in_scope=row.always_in_scope,
                    dd_master_ref=row.dd_master_ref,
                )
                for row in library.deck(deck_id).rows
            ]
            for deck_id in sorted(library.decks)
        },
    )
