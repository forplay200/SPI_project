import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it } from "vitest";

import { DraftReviewPage } from "../pages/DraftReviewPage";
import { mockApi, project, renderProjectPage } from "./helpers";

it("persists checklist progress and identifies restricted smoke drafts", async () => {
  mockApi((path) =>
    path.endsWith("/projects/project-test")
      ? project
      : {
          path: "output/draft/demo-smoke_draft.mp4",
          filename: "demo-smoke_draft.mp4",
          sha256: "a".repeat(64),
          metadata: {
            duration_seconds: 18,
            width: 1280,
            height: 720,
            fps: 30,
            has_video: true,
            has_audio: true,
            video_codec: "h264",
            audio_codec: "aac",
          },
          renderer_used: "moviepy",
          sync_state: "needs_human_confirmation",
          compliance_state: "SMOKE_NON_COMPLIANT",
          human_review_required: true,
          common_overlap_duration: 4.44,
          total_event_coverage: 20,
          maximum_renderable_duration: 18,
        },
  );
  renderProjectPage(<DraftReviewPage />, "/projects/project-test/draft-review");
  expect(
    await screen.findByText("Restricted technical draft"),
  ).toBeInTheDocument();
  const checkbox = screen.getByRole("checkbox", { name: /Draft opens/i });
  await userEvent.click(checkbox);
  expect(
    JSON.parse(localStorage.getItem("review-checklist-project-test") ?? "{}")
      .output_opens,
  ).toBe(true);
  expect(screen.getByRole("option", { name: /Approved/i })).toBeDisabled();
  expect(screen.getByText("Common Synchronized Overlap")).toBeInTheDocument();
});
