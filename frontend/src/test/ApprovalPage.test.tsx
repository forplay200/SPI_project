import { screen } from "@testing-library/react";
import { expect, it } from "vitest";

import { ApprovalPage } from "../pages/ApprovalPage";
import { mockApi, renderProjectPage } from "./helpers";

it("explains every blocker and disables approval", async () => {
  mockApi(() => ({
    eligible: false,
    blockers: [
      "Smoke drafts do not satisfy the duration policy.",
      "Synchronisation has not been manually verified.",
    ],
    draft_sha256: "b".repeat(64),
    review_status: "changes_requested",
    sync_status: "needs_human_confirmation",
    compliance_status: "smoke",
  }));
  renderProjectPage(<ApprovalPage />, "/projects/project-test/approval");
  expect(await screen.findByText("Approval is blocked")).toBeInTheDocument();
  expect(screen.getByText(/Smoke drafts/)).toBeInTheDocument();
  expect(screen.getByText(/Synchronisation has not/)).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: /Approve Exact Reviewed Draft/i }),
  ).toBeDisabled();
});
