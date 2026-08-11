import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it } from "vitest";

import { SynchronisationPage } from "../pages/SynchronisationPage";
import { mockApi, project, renderProjectPage } from "./helpers";

it("keeps automatic transients unverified and exposes confirmation controls", async () => {
  mockApi((path) =>
    path.endsWith("/projects/project-test")
      ? project
      : {
          master_camera: "camera_01",
          cue_type: "shared_audio_transient",
          cue_description:
            "Local shared transient; not automatically accepted as a clap.",
          acceptance_status: "needs_human_confirmation",
          clap_timestamps: { camera_01: 2.1, camera_02: 22.4 },
          verification_threshold_ms: 100,
          requires_human_verification: true,
          manual_confirmations: {},
          duration_metrics: {
            common_overlap_duration: 4.44,
            total_event_coverage: 105.11,
            maximum_renderable_duration: 96,
          },
          camera_analyses: [
            {
              camera_id: "camera_01",
              candidates: [
                {
                  timestamp_seconds: 2.1,
                  confidence: 0.82,
                  cue_type: "shared_audio_transient",
                  supporting_metric: 0.82,
                },
              ],
              selected_timestamp_seconds: 2.1,
              confidence: 0.82,
              state: "shared_audio_transient",
              requires_human_verification: true,
              warnings: ["Not a verified clap"],
            },
            {
              camera_id: "camera_02",
              candidates: [
                {
                  timestamp_seconds: 22.4,
                  confidence: 0.8,
                  cue_type: "shared_audio_transient",
                  supporting_metric: 0.8,
                },
              ],
              selected_timestamp_seconds: 22.4,
              confidence: 0.8,
              state: "shared_audio_transient",
              requires_human_verification: true,
              warnings: [],
            },
          ],
          pairwise_alignment: [
            {
              camera_a: "camera_01",
              camera_b: "camera_02",
              state: "NEEDS_HUMAN_VERIFICATION",
              selected_offset_seconds: null,
              reason: "Large offset lacks stable evidence",
              alternatives: [
                {
                  offset_seconds: 20.3,
                  confidence: 0.4,
                  audio_correlation: 0.5,
                  overlap_seconds: 40,
                  overlap_ratio: 0.7,
                  offset_stability: 0.2,
                  supported_windows: 1,
                  large_offset: true,
                  accepted_for_automatic_use: false,
                  reason: "Needs human verification",
                },
              ],
            },
          ],
        },
  );
  renderProjectPage(
    <SynchronisationPage />,
    "/projects/project-test/synchronisation",
  );
  expect(
    await screen.findByText("Human verification required"),
  ).toBeInTheDocument();
  expect(screen.getAllByRole("button", { name: /Confirm Cue/i })).toHaveLength(
    2,
  );
  expect(
    screen.getAllByRole("button", { name: /Reject Candidate/i }),
  ).toHaveLength(2);
  expect(
    screen.getAllByRole("button", { name: /Reject Candidate/i })[0],
  ).toBeDisabled();
  const rejectionReason = screen.getAllByLabelText(
    "Reason for rejecting candidate",
  )[0];
  await userEvent.type(rejectionReason, "The cue is not the deliberate clap.");
  expect(
    screen.getAllByRole("button", { name: /Reject Candidate/i })[0],
  ).toBeEnabled();
  expect(
    screen.getByText("Multi-window offset diagnostics"),
  ).toBeInTheDocument();
  expect(screen.getByText("105.11 s")).toBeInTheDocument();
  expect(
    screen.getByLabelText(/acknowledge that the large offset/i),
  ).toBeInTheDocument();
  await userEvent.click(screen.getAllByRole("button", { name: /2.100 s/i })[0]);
});
