import { fireEvent, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import { EvidencePage } from "../pages/EvidencePage";
import { mockApi, renderProjectPage } from "./helpers";

it("lists evidence with duration provenance and file actions", async () => {
  mockApi((path) =>
    path.endsWith("/analysis")
      ? {
          videos: [],
          selected_camera_ids: [],
          master_camera: null,
          suggested_camera_ids: [],
          suggested_master_camera: null,
          grouping: {},
          common_overlap_duration: 4.44,
          total_event_coverage: 105.11,
          maximum_renderable_duration: 96,
        }
      : [
          {
            id: "grouping",
            label: "Camera grouping",
            category: "camera_grouping",
            path: "evidence/ui/camera_grouping.json",
            media_type: "application/json",
            exists: true,
          },
        ],
  );
  renderProjectPage(<EvidencePage />, "/projects/project-test/evidence");
  expect(await screen.findAllByText("Camera grouping")).toHaveLength(2);
  expect(
    screen.getByRole("button", { name: "Expand JSON" }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: /Copy path/i }),
  ).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /Download/i })).toHaveAttribute(
    "download",
  );
  expect(screen.getByText("105.11 s")).toBeInTheDocument();
});

it("disables missing downloads and reports clipboard failures", async () => {
  mockApi((path) =>
    path.endsWith("/analysis")
      ? {
          videos: [],
          selected_camera_ids: [],
          master_camera: null,
          suggested_camera_ids: [],
          suggested_master_camera: null,
          grouping: {},
          common_overlap_duration: null,
          total_event_coverage: null,
          maximum_renderable_duration: null,
        }
      : [
          {
            id: "missing-review",
            label: "Review record",
            category: "review",
            path: "evidence/ui/review.json",
            media_type: "application/json",
            exists: false,
          },
        ],
  );
  vi.mocked(navigator.clipboard.writeText).mockRejectedValueOnce(
    new Error("Clipboard permission denied"),
  );

  renderProjectPage(<EvidencePage />, "/projects/project-test/evidence");
  expect(await screen.findByText("Review record")).toBeInTheDocument();

  const download = screen.getByRole("button", { name: /Download/i });
  expect(download).toBeDisabled();
  expect(
    screen.queryByRole("link", { name: /Download/i }),
  ).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /Copy path/i }));
  await waitFor(() =>
    expect(screen.getByText(/could not be copied/i)).toBeInTheDocument(),
  );
});
