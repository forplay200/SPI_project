import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import type { Project } from "../api/types";
import { ProjectProvider } from "../context/ProjectContext";

export const project: Project = {
  id: "project-test",
  title: "Graduation Demo",
  input_folder: "input",
  duration_seconds: 18,
  resolution: "1280x720",
  draft_mode: true,
  smoke_mode: true,
  credits: "Edited by the Project Team",
  credits_duration: 4,
  created_at: "2026-07-29T00:00:00Z",
  updated_at: "2026-07-29T00:00:00Z",
  outcome: "NEEDS_SYNC_CONFIRMATION",
  current_step: 5,
  artifacts: {},
  latest_job_id: null,
};

export function jsonResponse(value: unknown, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(value), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

export function mockApi(handler: (path: string, method: string) => unknown) {
  return vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
    const url =
      typeof input === "string"
        ? input
        : input instanceof Request
          ? input.url
          : input.toString();
    const value = handler(
      url.replace(/^.*\/api/, "/api"),
      init?.method ?? "GET",
    );
    return jsonResponse(value);
  });
}

export function renderProjectPage(element: ReactElement, path: string) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route
            path="/projects/:projectId/*"
            element={<ProjectProvider>{element}</ProjectProvider>}
          />
          <Route
            path="/"
            element={<ProjectProvider>{element}</ProjectProvider>}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
