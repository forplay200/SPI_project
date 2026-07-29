import { LoaderCircle } from "lucide-react";

import type { Job } from "../api/types";
import { Alert } from "./ui/alert";
import { Progress } from "./ui/progress";

export function JobProgress({ job }: { job: Job }) {
  if (job.status === "FAILED")
    return (
      <Alert tone="danger" title="Processing failed">
        {job.error ?? job.message}
      </Alert>
    );
  if (job.status === "CANCELLED")
    return (
      <Alert tone="warning" title="Job cancelled">
        {job.warning ?? job.message}
      </Alert>
    );
  if (job.status === "COMPLETED")
    return (
      <Alert tone="success" title="Stage complete">
        {job.message}
      </Alert>
    );
  return (
    <div
      className="rounded-xl border border-primary/20 bg-primary-soft p-5"
      aria-live="polite"
    >
      <div className="mb-4 flex items-center gap-3 text-primary-hover">
        <LoaderCircle className="h-5 w-5 animate-spin" />
        <div>
          <p className="font-semibold">{job.status.replaceAll("_", " ")}</p>
          <p className="text-sm">{job.message}</p>
        </div>
        <span className="ml-auto text-sm font-bold">{job.progress}%</span>
      </div>
      <Progress value={job.progress} />
    </div>
  );
}
