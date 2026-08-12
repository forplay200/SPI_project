import { fireEvent, screen, waitFor } from "@testing-library/react";
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

it("requires confirmation before promoting the exact reviewed draft", async () => {
  const fetchSpy = mockApi((_path, method) =>
    method === "POST"
      ? { sha256: "a".repeat(64) }
      : {
          eligible: true,
          blockers: [],
          draft_sha256: "a".repeat(64),
          review_status: "approved",
          sync_status: "manually_verified_clap",
          compliance_status: "compliant",
        },
  );

  renderProjectPage(<ApprovalPage />, "/projects/project-test/approval");
  const approveButton = await screen.findByRole("button", {
    name: /Approve Exact Reviewed Draft/i,
  });
  fireEvent.click(approveButton);

  expect(screen.getByText("Confirm exact-byte promotion")).toBeInTheDocument();
  expect(
    fetchSpy.mock.calls.filter(([, options]) => options?.method === "POST"),
  ).toHaveLength(0);

  fireEvent.click(screen.getByRole("button", { name: /Confirm Promotion/i }));
  await waitFor(() =>
    expect(
      fetchSpy.mock.calls.filter(([, options]) => options?.method === "POST"),
    ).toHaveLength(1),
  );
  expect(
    await screen.findByText(/Final approval completed/),
  ).toBeInTheDocument();
});
