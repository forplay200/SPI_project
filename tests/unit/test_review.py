from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.errors import ApprovalError, ReviewError
from src.review import (
    REVIEW_CHECKLIST_ITEMS,
    promote_approved_draft,
    record_review,
)


class ReviewTests(unittest.TestCase):
    def test_approval_is_bound_to_exact_draft_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = root / "output" / "draft" / "project_draft.mp4"
            draft.parent.mkdir(parents=True)
            draft.write_bytes(b"original draft")
            record_path = root / "evidence" / "approval.json"
            record = record_review(
                project="project",
                draft_path=draft,
                reviewer="Human Reviewer",
                decision="approved",
                comments="Watched completely.",
                checklist={item: True for item in REVIEW_CHECKLIST_ITEMS},
                record_path=record_path,
            )
            final = promote_approved_draft(
                draft_path=draft,
                review_record_path=record_path,
                final_directory=root / "output" / "final",
            )
            self.assertEqual(final.read_bytes(), b"original draft")
            self.assertEqual(
                record.draft_sha256, json.loads(record_path.read_text())["draft_sha256"]
            )

    def test_changed_draft_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = root / "output" / "draft" / "project_draft.mp4"
            draft.parent.mkdir(parents=True)
            draft.write_bytes(b"reviewed bytes")
            record_path = root / "review.json"
            record_review(
                project="project",
                draft_path=draft,
                reviewer="Reviewer",
                decision="approved",
                comments="",
                checklist={item: True for item in REVIEW_CHECKLIST_ITEMS},
                record_path=record_path,
            )
            draft.write_bytes(b"changed bytes")
            with self.assertRaises(ApprovalError) as raised:
                promote_approved_draft(
                    draft_path=draft,
                    review_record_path=record_path,
                    final_directory=root / "output" / "final",
                )
            self.assertIn("changed after review", str(raised.exception))

    def test_approved_decision_requires_complete_checklist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            draft = Path(directory) / "output" / "draft" / "project_draft.mp4"
            draft.parent.mkdir(parents=True)
            draft.write_bytes(b"draft")
            checklist = {item: True for item in REVIEW_CHECKLIST_ITEMS}
            checklist["privacy_checked"] = False
            with self.assertRaises(ReviewError):
                record_review(
                    project="project",
                    draft_path=draft,
                    reviewer="Reviewer",
                    decision="approved",
                    comments="",
                    checklist=checklist,
                    record_path=Path(directory) / "record.json",
                )

    def test_tampered_approved_record_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = root / "output" / "draft" / "project_draft.mp4"
            draft.parent.mkdir(parents=True)
            draft.write_bytes(b"draft")
            record_path = root / "record.json"
            record_review(
                project="project",
                draft_path=draft,
                reviewer="Reviewer",
                decision="approved",
                comments="",
                checklist={item: True for item in REVIEW_CHECKLIST_ITEMS},
                record_path=record_path,
            )
            data = json.loads(record_path.read_text(encoding="utf-8"))
            data["checklist"]["privacy_checked"] = False
            record_path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ApprovalError) as raised:
                promote_approved_draft(
                    draft_path=draft,
                    review_record_path=record_path,
                    final_directory=root / "output" / "final",
                )
            self.assertIn("unchecked item", str(raised.exception))

    def test_smoke_and_unverified_sync_drafts_cannot_be_approved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (
                "project-smoke_draft.mp4",
                "project-unverified-sync_draft.mp4",
            ):
                draft = root / "output" / "draft" / name
                draft.parent.mkdir(parents=True, exist_ok=True)
                draft.write_bytes(b"technical draft")
                with self.assertRaises(ReviewError) as raised:
                    record_review(
                        project="project",
                        draft_path=draft,
                        reviewer="Reviewer",
                        decision="approved",
                        comments="",
                        checklist={item: True for item in REVIEW_CHECKLIST_ITEMS},
                        record_path=root / f"{name}.json",
                    )
                self.assertIn("cannot be approved", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
