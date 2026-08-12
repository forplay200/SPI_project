import { FileJson2, Film, HardDrive, ShieldCheck } from "lucide-react";
import { NavLink, Outlet, useParams } from "react-router-dom";

import { useCurrentProject } from "../context/ProjectContext";
import { Badge } from "./ui/badge";
import { WorkflowStepper } from "./WorkflowStepper";

export function AppShell() {
  const { projectId } = useParams();
  const { data: project } = useCurrentProject();
  return (
    <div className="min-h-screen bg-background">
      <a
        href="#main-content"
        className="fixed left-4 top-3 z-50 -translate-y-20 rounded-lg bg-primary px-4 py-2 font-semibold text-white shadow-lg transition-transform focus:translate-y-0"
      >
        Skip to main content
      </a>
      <header className="sticky top-0 z-30 border-b border-border bg-white/95 backdrop-blur">
        <div className="mx-auto flex min-h-16 max-w-[1600px] items-center justify-between gap-4 px-4 sm:px-6">
          <NavLink
            to="/"
            className="flex items-center gap-3 text-ink"
            aria-label="Graduation video workflow home"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-white">
              <Film className="h-5 w-5" />
            </span>
            <span>
              <strong className="block text-sm sm:text-base">
                Graduation Video Workflow
              </strong>
              <span className="hidden text-xs text-ink-muted sm:block">
                Guided local automation
              </span>
            </span>
          </NavLink>
          <div className="flex items-center gap-2">
            {project ? (
              <Badge tone={project.smoke_mode ? "warning" : "primary"}>
                {project.smoke_mode ? "Smoke mode" : "Draft mode"}
              </Badge>
            ) : null}
            <Badge tone="success">
              <HardDrive className="mr-1 h-3.5 w-3.5" /> Local only
            </Badge>
          </div>
        </div>
      </header>
      <div className="mx-auto grid max-w-[1600px] lg:grid-cols-[270px_1fr]">
        <aside className="border-b border-border bg-white lg:min-h-[calc(100vh-4rem)] lg:border-b-0 lg:border-r">
          <div className="lg:sticky lg:top-16">
            <WorkflowStepper />
            {projectId ? (
              <div className="hidden border-t border-border p-4 lg:block">
                <NavLink
                  to={`/projects/${projectId}/evidence`}
                  className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-ink-muted hover:bg-subtle hover:text-ink"
                >
                  <FileJson2 className="h-4 w-4" /> Evidence
                </NavLink>
                <p className="mt-4 flex gap-2 px-3 text-xs leading-5 text-ink-faint">
                  <ShieldCheck className="h-4 w-4 shrink-0" /> Final approval
                  always remains a separate human action.
                </p>
              </div>
            ) : null}
          </div>
        </aside>
        <main
          id="main-content"
          tabIndex={-1}
          className="min-w-0 p-4 sm:p-6 lg:p-8"
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
