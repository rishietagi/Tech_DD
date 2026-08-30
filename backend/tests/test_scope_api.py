"""The Phase 2 scope endpoints: preview, versions, row override, library."""

from fastapi.testclient import TestClient

from tests.test_engagement_flow import SECTIONS_PAYLOAD


def _filed_engagement(client: TestClient) -> str:
    response = client.post("/api/v1/engagements", json={"deal_name": "Project Atlas"})
    engagement_id = response.json()["id"]
    for section, payload in SECTIONS_PAYLOAD.items():
        client.patch(f"/api/v1/engagements/{engagement_id}/intake/{section}", json=payload)
    client.post(f"/api/v1/engagements/{engagement_id}/submit")
    return engagement_id


def _draft_engagement(client: TestClient, **sections) -> str:
    response = client.post("/api/v1/engagements", json={"deal_name": "Project Draft"})
    engagement_id = response.json()["id"]
    for section, payload in sections.items():
        client.patch(f"/api/v1/engagements/{engagement_id}/intake/{section}", json=payload)
    return engagement_id


# --------------------------------------------------------------------------- preview


def test_preview_works_on_an_empty_draft(client: TestClient) -> None:
    """It powers a live panel while the user types, so it must never 422."""
    engagement_id = _draft_engagement(client)
    response = client.post(f"/api/v1/engagements/{engagement_id}/scope/preview")
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["is_complete"] is False
    assert body["classification"]["confidence"] == "low"
    assert body["deck"] in ("product", "enterprise", "blended")


def test_preview_reflects_answers_as_they_arrive(client: TestClient) -> None:
    engagement_id = _draft_engagement(client)
    before = client.post(f"/api/v1/engagements/{engagement_id}/scope/preview").json()

    client.patch(
        f"/api/v1/engagements/{engagement_id}/intake/technology",
        json={"tech_is_product": "Yes, the software is the product"},
    )
    client.patch(
        f"/api/v1/engagements/{engagement_id}/intake/target",
        json={"digital_maturity": "Digital native"},
    )
    after = client.post(f"/api/v1/engagements/{engagement_id}/scope/preview").json()

    assert after["classification"]["computed_dd_mix"] > before["classification"]["computed_dd_mix"]


def test_preview_honours_a_declared_archetype(client: TestClient) -> None:
    engagement_id = _draft_engagement(
        client, objectives={"dd_type_preference": "Enterprise IT DD"}
    )
    body = client.post(f"/api/v1/engagements/{engagement_id}/scope/preview").json()
    assert body["deck"] == "enterprise"
    assert body["classification"]["override_applied"] is True


def test_preview_marks_a_complete_intake(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    body = client.post(f"/api/v1/engagements/{engagement_id}/scope/preview").json()
    assert body["is_complete"] is True


def test_preview_does_not_persist_a_scope(client: TestClient) -> None:
    engagement_id = _draft_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/scope/preview")
    versions = client.get(f"/api/v1/engagements/{engagement_id}/scope/versions")
    assert versions.json() == []


# ------------------------------------------------------------------------ generate


def test_generate_accepts_an_explicit_generator(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    response = client.post(
        f"/api/v1/engagements/{engagement_id}/scope", json={"generator": "rules"}
    )
    assert response.status_code == 200
    assert response.json()["generator"] == "rules"


def test_generate_works_without_a_body(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    response = client.post(f"/api/v1/engagements/{engagement_id}/scope")
    assert response.status_code == 200


def test_regenerating_creates_a_new_version(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    first = client.post(f"/api/v1/engagements/{engagement_id}/scope").json()
    second = client.post(f"/api/v1/engagements/{engagement_id}/scope").json()

    assert first["version"] == 1
    assert second["version"] == 2
    # Versioning never destroys the prior scope.
    assert len(client.get(f"/api/v1/engagements/{engagement_id}/scope/versions").json()) == 2


def test_generation_populates_the_denorm_for_filtering(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/scope")
    listed = client.get("/api/v1/engagements").json()["items"][0]
    assert listed["denorm"]["dd_type"] == "product"
    assert listed["denorm"]["dd_mix"] is not None


# ------------------------------------------------------------------ single version


def test_fetching_a_specific_version(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/scope")
    client.post(f"/api/v1/engagements/{engagement_id}/scope")

    response = client.get(f"/api/v1/engagements/{engagement_id}/scope/1")
    assert response.status_code == 200
    assert response.json()["version"] == 1


def test_missing_version_returns_404(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/scope")
    response = client.get(f"/api/v1/engagements/{engagement_id}/scope/99")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "no_scope_version"


def test_versions_route_is_not_shadowed_by_the_version_route(client: TestClient) -> None:
    """`/versions` is declared before `/{version}`; confirm it still resolves."""
    engagement_id = _filed_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/scope")
    response = client.get(f"/api/v1/engagements/{engagement_id}/scope/versions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# --------------------------------------------------------------------- overrides


def test_row_override_changes_the_tier_and_keeps_the_original(client: TestClient) -> None:
    """DD_master G6 — the human overrides the engine, visibly."""
    engagement_id = _filed_engagement(client)
    scope = client.post(f"/api/v1/engagements/{engagement_id}/scope").json()
    row_id = scope["payload"]["rows"][0]["id"]
    original_tier = scope["payload"]["rows"][0]["tier"]

    response = client.patch(
        f"/api/v1/engagements/{engagement_id}/scope/1/rows/{row_id}",
        json={"tier": 1, "reason": "Client has already had this area reviewed externally."},
    )
    assert response.status_code == 200

    edited = next(r for r in response.json()["payload"]["rows"] if r["id"] == row_id)
    assert edited["tier"] == 1
    assert edited["edited_by_human"] is True
    assert edited["original_tier"] == original_tier
    assert "already had this area reviewed" in edited["override_reason"]
    assert any("human override" in a for a in edited["adjustments"])


def test_row_override_can_retitle(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    scope = client.post(f"/api/v1/engagements/{engagement_id}/scope").json()
    row_id = scope["payload"]["rows"][0]["id"]
    original_title = scope["payload"]["rows"][0]["title"]

    response = client.patch(
        f"/api/v1/engagements/{engagement_id}/scope/1/rows/{row_id}",
        json={"title": "Architecture and scalability review"},
    )
    edited = next(r for r in response.json()["payload"]["rows"] if r["id"] == row_id)
    assert edited["title"] == "Architecture and scalability review"
    assert edited["original_title"] == original_title


def test_repeated_overrides_keep_the_engines_original(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    scope = client.post(f"/api/v1/engagements/{engagement_id}/scope").json()
    row_id = scope["payload"]["rows"][0]["id"]
    original_tier = scope["payload"]["rows"][0]["tier"]

    client.patch(f"/api/v1/engagements/{engagement_id}/scope/1/rows/{row_id}", json={"tier": 1})
    response = client.patch(
        f"/api/v1/engagements/{engagement_id}/scope/1/rows/{row_id}", json={"tier": 3}
    )
    edited = next(r for r in response.json()["payload"]["rows"] if r["id"] == row_id)
    assert edited["tier"] == 3
    assert edited["original_tier"] == original_tier, "the engine's value must survive re-editing"


def test_override_of_an_unknown_row_returns_404(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/scope")
    response = client.patch(
        f"/api/v1/engagements/{engagement_id}/scope/1/rows/PD-99", json={"tier": 1}
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "row_not_found"


def test_override_survives_into_the_stored_scope(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    scope = client.post(f"/api/v1/engagements/{engagement_id}/scope").json()
    row_id = scope["payload"]["rows"][0]["id"]

    client.patch(
        f"/api/v1/engagements/{engagement_id}/scope/1/rows/{row_id}",
        json={"tier": 0, "reason": "Out of scope by client agreement."},
    )
    refetched = client.get(f"/api/v1/engagements/{engagement_id}/scope/1").json()
    edited = next(r for r in refetched["payload"]["rows"] if r["id"] == row_id)
    assert edited["tier"] == 0
    assert edited["tier_name"] == "Not in scope"


def test_regeneration_leaves_the_edited_version_intact(client: TestClient) -> None:
    """An edit survives regeneration as a recorded prior version (G6)."""
    engagement_id = _filed_engagement(client)
    scope = client.post(f"/api/v1/engagements/{engagement_id}/scope").json()
    row_id = scope["payload"]["rows"][0]["id"]
    client.patch(
        f"/api/v1/engagements/{engagement_id}/scope/1/rows/{row_id}", json={"tier": 1}
    )

    client.post(f"/api/v1/engagements/{engagement_id}/scope")  # v2

    v1 = client.get(f"/api/v1/engagements/{engagement_id}/scope/1").json()
    edited = next(r for r in v1["payload"]["rows"] if r["id"] == row_id)
    assert edited["edited_by_human"] is True
    assert edited["tier"] == 1


# ---------------------------------------------------------------- meta/workstreams


def test_workstream_library_is_served(client: TestClient) -> None:
    response = client.get("/api/v1/meta/workstreams")
    assert response.status_code == 200

    body = response.json()
    assert body["library_version"] == "1.0"
    assert body["source_owner"] == "KPMG India Services LLP"
    assert set(body["decks"]) == {"product", "enterprise"}
    assert len(body["decks"]["product"]) == 10
    assert len(body["decks"]["enterprise"]) == 9


def test_library_rows_carry_their_wording_and_reference(client: TestClient) -> None:
    body = client.get("/api/v1/meta/workstreams").json()
    for deck_rows in body["decks"].values():
        for row in deck_rows:
            assert row["title"].strip()
            assert row["lines"]
            assert row["dd_master_ref"]
