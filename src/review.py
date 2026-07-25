"""Human review records and checksum-bound final promotion."""

from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .errors import ApprovalError, ReviewError
from .evidence import sha256_file
from .json_utils import write_json_atomic
from .models import ReviewRecord

REVIEW_CHECKLIST_ITEMS = (
    "output_opens",
    "duration_valid",
    "clap_sync_within_threshold",
    "two_cameras_visible",
    "three_switches_visible",
    "title_readable",
    "credits_readable",
    "overlay_readable",
    "transition_visible",
    "important_moments_retained",
    "camera_choices_reasonable",
    "audio_continuity_acceptable",
    "privacy_checked",
    "asset_licences_checked",
)


def _require_draft_location(draft: Path) -> None:
    if (
        not draft.is_file()
        or "_draft" not in draft.stem
        or draft.parent.name != "draft"
        or draft.parent.parent.name != "output"
    ):
        raise ReviewError(
            "Human review requires an existing '_draft' file under output/draft/."
        )


def create_review_checklist(path: Path, *, draft_path: Path) -> None:
    _require_draft_location(draft_path.resolve())
    write_json_atomic(
        path,
        {
            "draft_path": str(draft_path.resolve()),
            "instructions": "Watch the complete draft and set each item to true only when verified.",
            "checklist": {item: False for item in REVIEW_CHECKLIST_ITEMS},
        },
    )


def load_checklist(path: Path) -> dict[str, bool]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReviewError(f"Review checklist does not exist: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ReviewError(f"Cannot read review checklist {path}: {exc}") from exc
    checklist = value.get("checklist") if isinstance(value, dict) else None
    if not isinstance(checklist, dict):
        raise ReviewError("Review checklist JSON must contain a checklist object.")
    missing = sorted(set(REVIEW_CHECKLIST_ITEMS) - set(checklist))
    unknown = sorted(set(checklist) - set(REVIEW_CHECKLIST_ITEMS))
    non_boolean = sorted(
        key for key, result in checklist.items() if not isinstance(result, bool)
    )
    errors: list[str] = []
    if missing:
        errors.append(f"Missing checklist items: {missing}.")
    if unknown:
        errors.append(f"Unknown checklist items: {unknown}.")
    if non_boolean:
        errors.append(f"Checklist values must be true or false: {non_boolean}.")
    if errors:
        raise ReviewError("Review checklist errors:\n- " + "\n- ".join(errors))
    return {key: bool(checklist[key]) for key in REVIEW_CHECKLIST_ITEMS}


def record_review(
    *,
    project: str,
    draft_path: Path,
    reviewer: str,
    decision: str,
    comments: str,
    checklist: dict[str, bool],
    record_path: Path,
) -> ReviewRecord:
    draft = draft_path.resolve()
    _require_draft_location(draft)
    if not reviewer.strip():
        raise ReviewError("Reviewer name must be non-empty.")
    if decision not in {"approved", "changes_requested"}:
        raise ReviewError("Decision must be 'approved' or 'changes_requested'.")
    if decision == "approved" and any(
        marker in draft.stem.casefold() for marker in ("smoke", "unverified-sync")
    ):
        raise ReviewError(
            "Smoke and unverified-sync drafts are technical review artefacts and "
            "cannot be approved as final submissions."
        )
    missing = set(REVIEW_CHECKLIST_ITEMS) - set(checklist)
    if missing:
        raise ReviewError(f"Checklist is missing required items: {sorted(missing)}.")
    if decision == "approved" and not all(
        checklist[item] for item in REVIEW_CHECKLIST_ITEMS
    ):
        failed = [item for item in REVIEW_CHECKLIST_ITEMS if not checklist[item]]
        raise ReviewError(
            f"An approved review requires every checklist item to be true; failed: {failed}."
        )
    record = ReviewRecord(
        project=project,
        draft_path=str(draft),
        draft_sha256=sha256_file(draft),
        reviewer=reviewer.strip(),
        decision=decision,  # type: ignore[arg-type]
        comments=comments.strip(),
        reviewed_at=datetime.now(timezone.utc).isoformat(),
        checklist={item: checklist[item] for item in REVIEW_CHECKLIST_ITEMS},
    )
    write_json_atomic(record_path, asdict(record))
    return record


def load_review_record(path: Path) -> ReviewRecord:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ApprovalError(f"Review record does not exist: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ApprovalError(f"Cannot read review record {path}: {exc}") from exc
    try:
        record = ReviewRecord(**value)
    except (TypeError, ValueError) as exc:
        raise ApprovalError(f"Review record has an invalid structure: {path}") from exc
    errors: list[str] = []
    if record.decision not in {"approved", "changes_requested"}:
        errors.append("decision is unsupported")
    if not record.reviewer.strip():
        errors.append("reviewer is empty")
    if not re.fullmatch(r"[0-9a-f]{64}", record.draft_sha256):
        errors.append("draft_sha256 is not a lowercase SHA-256 value")
    if set(record.checklist) != set(REVIEW_CHECKLIST_ITEMS):
        errors.append("checklist keys do not match the required review checklist")
    elif any(not isinstance(value, bool) for value in record.checklist.values()):
        errors.append("checklist values must be true or false")
    elif record.decision == "approved" and not all(record.checklist.values()):
        errors.append("approved review contains an unchecked item")
    if errors:
        raise ApprovalError(
            "Review record validation errors: " + "; ".join(errors) + "."
        )
    return record


def promote_approved_draft(
    *,
    draft_path: Path,
    review_record_path: Path,
    final_directory: Path,
) -> Path:
    """Copy the exact reviewed bytes to final only while the checksum remains valid."""
    draft = draft_path.resolve()
    try:
        _require_draft_location(draft)
    except ReviewError as exc:
        raise ApprovalError(str(exc)) from exc
    record = load_review_record(review_record_path)
    if record.decision != "approved":
        raise ApprovalError(
            "Only a review with decision 'approved' can promote a draft."
        )
    if Path(record.draft_path).resolve() != draft:
        raise ApprovalError("Review record is bound to a different draft path.")
    current_hash = sha256_file(draft)
    if current_hash != record.draft_sha256:
        raise ApprovalError(
            "Draft SHA-256 changed after review; create a new review before promotion."
        )
    expected_final_directory = draft.parent.parent / "final"
    if final_directory.resolve() != expected_final_directory.resolve():
        raise ApprovalError(
            f"Approved files may only be promoted to {expected_final_directory}."
        )
    final_directory.mkdir(parents=True, exist_ok=True)
    final_name = draft.name.replace("_draft", "_final", 1)
    final_path = final_directory / final_name
    if final_path.exists():
        if sha256_file(final_path) == current_hash:
            return final_path
        raise ApprovalError(
            f"Final output already exists with different bytes: {final_path}"
        )
    temp_path = final_directory / f".{final_path.stem}-{uuid4().hex}.partial.mp4"
    try:
        shutil.copy2(draft, temp_path)
        if sha256_file(temp_path) != current_hash:
            raise ApprovalError("Checksum changed while copying the approved draft.")
        os.replace(temp_path, final_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return final_path
