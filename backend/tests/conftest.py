import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Pin the test environment BEFORE app.core.config is imported, so a developer's local
# .env cannot change what the suite exercises. Without this, SCOPE_GENERATOR=llm makes
# the API tests call the live Gemini endpoint: slow, billable, and dependent on model
# output. The LLM layer is covered by mocked tests in test_llm.py instead.
os.environ["SCOPE_GENERATOR"] = "rules"
os.environ["GEMINI_API_KEY"] = ""

from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _no_live_llm_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail loudly if a test ever constructs a real Gemini client."""

    def _forbidden(*args: object, **kwargs: object) -> None:  # noqa: ARG001 - signature must match
        raise AssertionError(
            "A test tried to construct a live Gemini client. Tests must mock the client "
            "(see tests/test_llm.py) — never call the API."
        )

    monkeypatch.setattr("google.genai.Client", _forbidden)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def _get_db_override() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
