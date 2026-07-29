import { screen } from "@testing-library/react";
import { expect, it } from "vitest";

import { WorkflowStepper } from "../components/WorkflowStepper";
import { mockApi, project, renderProjectPage } from "./helpers";

it("shows the approved six-step workflow and current progress", async () => {
  mockApi(() => ({ ...project, current_step: 4 }));
  renderProjectPage(<WorkflowStepper />, "/projects/project-test/editing-plan");
  expect(await screen.findByText("1 Footage")).toBeInTheDocument();
  expect(screen.getByText("2 Analysis")).toBeInTheDocument();
  expect(screen.getByText("3 Synchronisation")).toBeInTheDocument();
  expect(screen.getByText("4 Editing Plan")).toBeInTheDocument();
  expect(screen.getByText("5 Draft Review")).toBeInTheDocument();
  expect(screen.getByText("6 Approval")).toBeInTheDocument();
});
