import { screen } from "@testing-library/react";
import { expect, it } from "vitest";

import { CameraAnalysisPage } from "../pages/CameraAnalysisPage";
import { mockApi, project, renderProjectPage } from "./helpers";

it("shows selected cameras, excluded outputs, and pair evidence", async () => {
  mockApi((path) =>
    path.endsWith("/projects/project-test")
      ? project
      : {
          videos: [
            {
              camera_id: "camera_01",
              relative_path: "input/a.mp4",
              duration_seconds: 20,
              width: 1280,
              height: 720,
              display_rotation: 0,
              fps: 30,
              video_codec: "h264",
              has_audio: true,
              audio_codec: "aac",
              classification: "likely_source",
              usable: true,
              warnings: [],
            },
            {
              camera_id: null,
              relative_path: "input/final.mp4",
              duration_seconds: null,
              width: null,
              height: null,
              display_rotation: 0,
              fps: null,
              video_codec: null,
              has_audio: null,
              audio_codec: null,
              classification: "likely_derived_output",
              usable: false,
              warnings: ["Excluded by policy"],
            },
          ],
          selected_camera_ids: ["camera_01", "camera_02"],
          master_camera: "camera_01",
          suggested_camera_ids: [],
          suggested_master_camera: null,
          common_overlap_duration: 4.44,
          total_event_coverage: 125.11,
          maximum_renderable_duration: 120,
          grouping: {
            state: "CAMERA_GROUP_CONFIRMED",
            confidence: "high",
            reason: "Strong local evidence",
            best_score: 0.88,
            analysed_pair_count: 1,
            pair_scores: [
              {
                camera_a: "camera_01",
                camera_b: "camera_02",
                path_a: "a",
                path_b: "b",
                audio_correlation: 0.9,
                estimated_offset_seconds: 0.3,
                offset_stability: 0.95,
                shared_transient_count: 2,
                common_usable_duration_seconds: 19,
                derived_duplicate_likelihood: 0,
                total_score: 0.88,
                confidence: "high",
                accepted: true,
                reason: "Accepted from local evidence",
              },
            ],
          },
        },
  );
  renderProjectPage(<CameraAnalysisPage />, "/projects/project-test/analysis");
  expect(await screen.findByText("CAMERA GROUP CONFIRMED")).toBeInTheDocument();
  expect(screen.getByText("final.mp4", { exact: false })).toBeInTheDocument();
  expect(screen.getByText("Audio correlation")).toBeInTheDocument();
  expect(screen.getByText("Master: camera_01")).toBeInTheDocument();
  expect(screen.getByText("Common Synchronized Overlap")).toBeInTheDocument();
  expect(screen.getByText("125.11 s")).toBeInTheDocument();
  expect(screen.getByText("120.00 s")).toBeInTheDocument();
});

it("offers a low-confidence pair for explicit human verification", async () => {
  mockApi((path) =>
    path.endsWith("/projects/project-test")
      ? project
      : {
          videos: ["camera_01", "camera_02"].map((camera_id) => ({
            camera_id,
            relative_path: `input/${camera_id}.mp4`,
            duration_seconds: 90,
            width: 1280,
            height: 720,
            display_rotation: 0,
            fps: 30,
            video_codec: "h264",
            has_audio: true,
            audio_codec: "aac",
            classification: "likely_source",
            usable: true,
            warnings: [],
          })),
          selected_camera_ids: [],
          master_camera: null,
          suggested_camera_ids: ["camera_01", "camera_02"],
          suggested_master_camera: "camera_01",
          common_overlap_duration: null,
          total_event_coverage: null,
          maximum_renderable_duration: null,
          grouping: {
            state: "CAMERA_GROUP_LOW_CONFIDENCE",
            confidence: "low",
            reason: "Suggested for human verification",
            best_score: 0.38,
            analysed_pair_count: 1,
            pair_scores: [
              {
                camera_a: "camera_01",
                camera_b: "camera_02",
                path_a: "a",
                path_b: "b",
                audio_correlation: 0.2,
                estimated_offset_seconds: 0,
                offset_stability: 0,
                shared_transient_count: 0,
                common_usable_duration_seconds: 90,
                derived_duplicate_likelihood: 0,
                total_score: 0.38,
                confidence: "low",
                accepted: false,
                suggested: true,
                reason: "Below automatic threshold",
              },
            ],
          },
        },
  );
  renderProjectPage(<CameraAnalysisPage />, "/projects/project-test/analysis");
  expect(
    await screen.findByRole("button", {
      name: /Continue with Human Verification/i,
    }),
  ).toBeEnabled();
  expect(
    screen.getAllByText("Suggested for human verification", { exact: false }),
  ).toHaveLength(2);
});
