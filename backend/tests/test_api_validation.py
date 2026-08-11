from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.app.schemas.api import SyncRejectRequest


def test_sync_rejection_reason_is_trimmed() -> None:
    request = SyncRejectRequest(
        camera_id="camera_01", reason="  Wrong audible event  "
    )
    assert request.reason == "Wrong audible event"


def test_sync_rejection_reason_cannot_be_blank() -> None:
    with pytest.raises(ValidationError):
        SyncRejectRequest(camera_id="camera_01", reason="   ")
