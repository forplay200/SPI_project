import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ProjectSetupPage } from "../pages/ProjectSetupPage";
import { mockApi, project, renderProjectPage } from "./helpers";

describe("ProjectSetupPage", () => {
  it("creates a project and starts analysis from the primary action", async () => {
    const calls: string[] = [];
    mockApi((path, method) => {
      calls.push(`${method} ${path}`);
      if (path === "/api/projects") return project;
      if (path.endsWith("/analysis"))
        return {
          job_id: "job-1",
          project_id: project.id,
          status: "QUEUED",
          progress: 0,
          message: "Queued",
          current_step: 2,
          operation: "analysis",
          warning: null,
          error: null,
          result: null,
          created_at: "",
          updated_at: "",
        };
      if (path.includes("/jobs/"))
        return {
          job_id: "job-1",
          project_id: project.id,
          status: "COMPLETED",
          progress: 100,
          message: "Completed",
          current_step: 2,
          operation: "analysis",
          warning: null,
          error: null,
          result: {},
          created_at: "",
          updated_at: "",
        };
      if (path.endsWith("/projects/project-test")) return project;
      return {
        videos: [],
        selected_camera_ids: [],
        master_camera: null,
        grouping: {
          state: "NO_RELIABLE_CAMERA_GROUP",
          confidence: "low",
          reason: "No group",
          best_score: null,
          analysed_pair_count: 0,
          pair_scores: [],
        },
      };
    });
    renderProjectPage(<ProjectSetupPage />, "/");
    expect(
      screen.getByRole("heading", { name: "Set up your local project" }),
    ).toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: /Analyse Footage/i }),
    );
    await waitFor(() => expect(calls).toContain("POST /api/projects"));
    expect(calls).toContain("POST /api/projects/project-test/analysis");
  });

  it("shows compliant and smoke modes without hiding approval limits", () => {
    renderProjectPage(<ProjectSetupPage />, "/");
    expect(screen.getAllByText("Compliant draft")).toHaveLength(1);
    expect(screen.getAllByText("Smoke test")).toHaveLength(1);
    expect(screen.getByText(/never approval-eligible/i)).toBeInTheDocument();
  });

  it("explains invalid duration and closing-credit values before submission", async () => {
    const user = userEvent.setup();
    const fetch = mockApi(() => project);
    renderProjectPage(<ProjectSetupPage />, "/");

    const duration = screen.getByLabelText("Target duration (seconds)");
    await user.clear(duration);
    await user.type(duration, "181");
    await user.clear(screen.getByLabelText("Closing credit text"));
    const creditDuration = screen.getByLabelText("Credit duration");
    await user.type(creditDuration, "31");
    await user.click(screen.getByRole("button", { name: /Analyse Footage/i }));

    expect(
      await screen.findByText("Target duration cannot exceed 180 seconds"),
    ).toBeInTheDocument();
    expect(screen.getByText("Enter closing credit text")).toBeInTheDocument();
    expect(
      screen.getByText("Credit duration must be between 0.1 and 30 seconds"),
    ).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });
});
