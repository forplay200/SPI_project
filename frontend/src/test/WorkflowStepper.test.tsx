import { screen } from "@testing-library/react";
import { expect, it } from "vitest";

import { WorkflowStepper } from "../components/WorkflowStepper";
import { mockApi, project, renderProjectPage } from "./helpers";

it("shows the approved six-step workflow and current progress", async () => {
  mockApi(() => ({ ...project, current_step: 4 }));
  renderProjectPage(<WorkflowStepper />, "/projects/project-test/editing-plan");
  expect(
    await screen.findByRole("link", { name: /1 Footage.*completed/i }),
  ).toBeInTheDocument();
  expect(screen.getByText("2 Analysis")).toBeInTheDocument();
  expect(screen.getByText("3 Synchronisation")).toBeInTheDocument();
  expect(screen.getByText("4 Editing Plan")).toBeInTheDocument();
  expect(screen.getByText("5 Draft Review")).toBeInTheDocument();
  expect(screen.getByText("6 Approval")).toBeInTheDocument();
  expect(screen.getByText("1 Footage").closest("a")).toHaveAttribute(
    "href",
    "/projects/project-test/setup",
  );
  expect(screen.getByText("6 Approval").closest("a")).toBeNull();
  expect(screen.getByText("6 Approval").closest("div")).toHaveAttribute(
    "aria-disabled",
    "true",
  );
});
