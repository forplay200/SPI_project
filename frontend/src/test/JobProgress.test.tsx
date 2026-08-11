import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it } from "vitest";

import type { Job } from "../api/types";
import { JobProgress } from "../components/JobProgress";
import { mockApi } from "./helpers";

const job: Job = {
  job_id: "job-1",
  project_id: "project-1",
  operation: "analysis",
  status: "DISCOVERING",
  progress: 25,
  message: "Discovering local videos",
  current_step: 1,
  warning: null,
  error: null,
  result: null,
  created_at: "2026-08-01T00:00:00Z",
  updated_at: "2026-08-01T00:00:01Z",
};

it("cancels a running job and displays its terminal state", async () => {
  const user = userEvent.setup();
  const fetch = mockApi((path, method) =>
    path === "/api/jobs/job-1/cancel" && method === "POST"
      ? {
          ...job,
          status: "CANCELLED",
          message: "Cancellation requested",
          warning: "Cancellation takes effect at the next safe stage boundary.",
        }
      : job,
  );
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  render(
    <QueryClientProvider client={client}>
      <JobProgress job={job} />
    </QueryClientProvider>,
  );

  await user.click(screen.getByRole("button", { name: "Cancel job" }));

  expect(await screen.findByText("Job cancelled")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Cancel job" })).toBeNull();
  expect(fetch).toHaveBeenCalledWith(
    "/api/jobs/job-1/cancel",
    expect.objectContaining({ method: "POST" }),
  );
});
