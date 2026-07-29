import { Check, Circle, LockKeyhole } from "lucide-react";
import { NavLink, useParams } from "react-router-dom";

import { cn } from "../lib/utils";
import { useCurrentProject } from "../context/ProjectContext";

const steps = [
  ["Footage", "setup"],
  ["Analysis", "analysis"],
  ["Synchronisation", "synchronisation"],
  ["Editing Plan", "editing-plan"],
  ["Draft Review", "draft-review"],
  ["Approval", "approval"],
] as const;

export function WorkflowStepper() {
  const { projectId } = useParams();
  const { data: project } = useCurrentProject();
  const currentStep = project?.current_step ?? 1;
  return (
    <nav
      aria-label="Workflow steps"
      className="overflow-x-auto lg:overflow-visible"
    >
      <ol className="flex min-w-max gap-2 p-3 lg:min-w-0 lg:flex-col lg:gap-1">
        {steps.map(([label, path], index) => {
          const number = index + 1;
          const enabled =
            Boolean(projectId) && number <= Math.max(currentStep + 1, 2);
          const href = projectId ? `/projects/${projectId}/${path}` : "/";
          return (
            <li key={label}>
              <NavLink
                to={enabled ? href : "#"}
                aria-disabled={!enabled}
                onClick={(event) => {
                  if (!enabled) event.preventDefault();
                }}
                className={({ isActive }) =>
                  cn(
                    "group flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-semibold transition-colors",
                    isActive
                      ? "bg-primary-soft text-primary-hover"
                      : "text-ink-muted hover:bg-subtle hover:text-ink",
                    !enabled && "cursor-not-allowed opacity-55",
                  )
                }
              >
                <span
                  className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-full border text-xs",
                    number < currentStep
                      ? "border-success bg-success text-white"
                      : "border-border bg-white",
                  )}
                >
                  {number < currentStep ? (
                    <Check className="h-4 w-4" />
                  ) : !enabled ? (
                    <LockKeyhole className="h-3.5 w-3.5" />
                  ) : (
                    <Circle className="h-3.5 w-3.5 fill-current" />
                  )}
                </span>
                <span>
                  {number} {label}
                </span>
              </NavLink>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
