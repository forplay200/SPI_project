import { useMutation, useQueryClient } from "@tanstack/react-query";
import { LoaderCircle } from "lucide-react";

import { api } from "../api/client";
import type { Job } from "../api/types";
import { Alert } from "./ui/alert";
import { Button } from "./ui/button";
import { Progress } from "./ui/progress";

export function JobProgress({ job }: { job: Job }) {
  const queryClient = useQueryClient();
  const cancel = useMutation({
    mutationFn: () => api.cancelJob(job.job_id),
    onSuccess: (next) => queryClient.setQueryData(["job", job.job_id], next),
  });
  const currentJob = cancel.data ?? job;

  if (currentJob.status === "FAILED")
    return (
      <Alert tone="danger" title="Processing failed">
        {currentJob.error ?? currentJob.message}
      </Alert>
    );
  if (currentJob.status === "CANCELLED")
    return (
      <Alert tone="warning" title="Job cancelled">
        {currentJob.warning ?? currentJob.message}
      </Alert>
    );
  if (currentJob.status === "COMPLETED")
    return (
      <Alert tone="success" title="Stage complete">
        {currentJob.message}
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
          <p className="font-semibold">
            {currentJob.status.replaceAll("_", " ")}
          </p>
          <p className="text-sm">{currentJob.message}</p>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <span className="text-sm font-bold">{currentJob.progress}%</span>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => cancel.mutate()}
            disabled={cancel.isPending}
          >
            {cancel.isPending ? "Cancelling…" : "Cancel job"}
          </Button>
        </div>
      </div>
      <Progress value={currentJob.progress} />
      {cancel.error instanceof Error ? (
        <p className="mt-3 text-sm text-red-700" role="alert">
          {cancel.error.message}
        </p>
      ) : null}
    </div>
  );
}
