"""The IT landscape overview diagram — a layout-free model built from the inventories.

The sample report's "Overview of current IT landscape" has two panels: applications
(ERP-managed functions, then grouped function → product pairs, custom tools) and
infrastructure (backup targets, which platform runs what, the asset classes). This module
builds the *content* of that picture from the inventories only; the frontend draws it as
SVG and the PPTX export as native shapes, from the same model. **Nothing is drawn that
the inventories do not contain.**
"""

from collections import defaultdict
from typing import Any

from app.services.report.inputs import ReportInputs

BACKUP_CATEGORIES = {"Storage and backup"}


def landscape(inputs: ReportInputs) -> dict[str, Any]:
    apps = inputs.items("application")
    platforms = inputs.items("platform")
    names = {a.ref: a.name for a in apps}

    erp = [a for a in apps if a.text("category") == "ERP"]
    erp_block = None
    if erp:
        primary = erp[0]
        functions = [inputs.process_names.get(k, k) for k in primary.listed("processes")]
        erp_block = {"name": primary.name, "functions": functions}

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for app in apps:
        if erp and app is erp[0]:
            continue
        label = app.text("category") or "Other applications"
        detail = app.text("type") or app.text("vendor")
        groups[label].append({"name": app.name, "detail": detail})

    infra: dict[str, list[dict[str, Any]]] = defaultdict(list)
    backup: list[str] = []
    for platform in platforms:
        if platform.text("category") in BACKUP_CATEGORIES:
            backup.append(platform.name)
            continue
        label = platform.text("location") or platform.text("category") or "Other platforms"
        infra[label].append(
            {
                "name": platform.name,
                "detail": platform.text("lifecycle"),
                "hosts": [names.get(r, r) for r in platform.listed("apps_hosted")],
            }
        )

    return {
        "kind": "landscape",
        "erp": erp_block,
        "app_groups": [{"label": k, "items": v} for k, v in sorted(groups.items())],
        "infra_groups": [{"label": k, "items": v} for k, v in sorted(infra.items())],
        "backup": backup,
        "empty": not apps and not platforms,
    }
