from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from src.edl import load_edl, validate_edl
from src.render_plan import build_render_plan
from src.sync import apply_sync, load_sync_config
from src.validate_inputs import load_project_config


class ShippedExampleTests(unittest.TestCase):
    def test_project_sync_edl_and_render_plan_are_consistent(self) -> None:
        root = Path(__file__).resolve().parents[2]
        config = load_project_config(
            root / "config" / "project.json", require_camera_files=False
        )
        sync = load_sync_config(root / "config" / "sync.json")
        synthetic_metadata = tuple(
            replace(camera, duration_seconds=200, has_audio=True)
            for camera in config.cameras
        )
        synced = apply_sync(
            synthetic_metadata,
            sync,
            expected_master_camera=config.master_camera,
        )
        config = replace(config, cameras=synced)
        edl = load_edl(root / "edl" / "editing_decisions.json")
        validate_edl(edl, config)
        plan = build_render_plan(config, edl)
        self.assertEqual(plan.expected_duration_seconds, 72)
        self.assertEqual(plan.switch_count, 3)
        self.assertEqual(plan.camera_offsets["camera_close"], 0.0)


if __name__ == "__main__":
    unittest.main()
