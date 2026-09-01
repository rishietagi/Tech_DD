"""Shared-drive scanning — DEFERRED, wired at deployment.

The intent: walk the folder the client drops documents into, match each file to an IRL
request, and update the checklist automatically so the consultant does not maintain it by
hand.

Not built yet, deliberately. The matching rules need real files in front of us to
calibrate, and a scanner that guesses wrong is worse than no scanner: it would mark a
request satisfied when the document is missing or irrelevant, and nobody would notice
until the deal team went looking for it.

**The rules this must follow when it is built** (recorded here so they are not lost):

1. **A scan never overwrites a human-set status.** `IrlDocumentStatus.set_by_human`
   exists for exactly this. Someone who has looked at a document and made a judgement
   outranks a filename match.
2. **Record what was matched.** `matched_files` holds the filenames a status was inferred
   from, so a wrong call is visible and correctable rather than silent.
3. **Below the confidence threshold, propose nothing.** Leaving a request as
   `not_received` is honest; marking it received on a weak filename match is not.
4. **Never delete or move client files.** Read-only over the drive, always.

The likely matching strategy, for whoever picks this up: tokenise the filename and the
containing folder, score against `seed_text` and the question text (both stored on every
`IrlQuestion`), and use the per-function folder names as a strong hint. A test fixture
lives at `shared-drive/project-lighthouse/` — see `docs/phases/PHASE4_PLAN.md`.
"""

from app.core.errors import AppError


class ScannerNotImplemented(AppError):
    """Raised by the scan endpoint until the shared-drive walk is built."""

    def __init__(self) -> None:
        super().__init__(
            code="scan_not_implemented",
            message=(
                "Shared-drive scanning is not connected yet. It is wired at deployment, "
                "when the drive path and matching rules are configured. Until then, set "
                "each document's status by hand on the checklist."
            ),
            status_code=501,
        )


def scan_shared_drive(_engagement_id: str) -> None:
    """Walk the drive and update statuses. Not implemented — see the module docstring.

    The argument is kept so the eventual implementation has the signature its caller
    already uses.
    """
    raise ScannerNotImplemented()
