import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it } from "vitest";

import { EditingPlanPage } from "../pages/EditingPlanPage";
import { mockApi, project, renderProjectPage } from "./helpers";

it("renders an explainable timeline and revalidates local edits", async () => {
  const edl = {
    project: "demo-unverified-sync-smoke",
    common_overlap_duration: 4.44,
    total_event_coverage: 20,
    maximum_renderable_duration: 16,
    timeline: [0, 1, 2, 3].map((index) => ({
      id: `shot-${index + 1}`,
      start: index * 4,
      end: (index + 1) * 4,
      camera: index % 2 ? "camera_02" : "camera_01",
      reason: `Rule reason ${index + 1}`,
      action: index === 0 ? "fade_in" : index === 3 ? "fade_to_black" : "cut",
      ...(index === 1
        ? { overlay: { type: "lower_third", text: "Graduation" } }
        : {}),
    })),
  };
  mockApi((path) => {
    if (path.endsWith("/projects/project-test")) return project;
    if (path.endsWith("/analysis"))
      return {
        videos: [],
        selected_camera_ids: [],
        master_camera: null,
        grouping: {},
      };
    return edl;
  });
  renderProjectPage(<EditingPlanPage />, "/projects/project-test/editing-plan");
  expect(await screen.findByText("Simplified timeline")).toBeInTheDocument();
  expect(
    screen.getByText("Target exceeds renderable coverage"),
  ).toBeInTheDocument();
  expect(screen.getByText("Rule reason 1")).toBeInTheDocument();
  const firstReason = screen.getAllByLabelText("Decision reason", {
    selector: "textarea",
  })[0];
  await userEvent.clear(firstReason);
  expect(screen.getByText(/reason is required/i)).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: /Save & Validate/i }),
  ).toBeDisabled();
});
