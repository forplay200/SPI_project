import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronRight, FileCheck2, Play, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import { api } from "../api/client";
import { JobProgress } from "../components/JobProgress";
import { DurationMetricsPanel } from "../components/DurationMetricsPanel";
import { PageHeader } from "../components/PageHeader";
import {
  ReviewChecklist,
  emptyChecklist,
  isReviewChecklistState,
  type ReviewChecklistState,
} from "../components/ReviewChecklist";
import { Alert } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader } from "../components/ui/card";
import { Input, Label, Select, Textarea } from "../components/ui/form";
import { useCurrentProject } from "../context/ProjectContext";
import { useJob } from "../hooks/useJob";
import { readStoredJson, writeStoredJson } from "../lib/storage";
import { formatStatusLabel } from "../lib/utils";

export function DraftReviewPage() {
  const { projectId = "" } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: project } = useCurrentProject();
  const initialJob =
    (location.state as { jobId?: string } | null)?.jobId ??
    (project?.current_step === 5 ? project.latest_job_id : null);
  const [jobId, setJobId] = useState<string | null>(initialJob ?? null);
  const job = useJob(jobId);
  const complete = job.data?.status === "COMPLETED";
  const draft = useQuery({
    queryKey: ["draft", projectId],
    queryFn: () => api.getDraft(projectId),
    enabled: complete || !jobId,
    retry: false,
  });
  const storageKey = `review-checklist-${projectId}`;
  const [checklist, setChecklist] = useState<ReviewChecklistState>(() =>
    readStoredJson(storageKey, emptyChecklist(), isReviewChecklistState),
  );
  const [reviewer, setReviewer] = useState("");
  const [comments, setComments] = useState("");
  const [decision, setDecision] = useState<"approved" | "changes_requested">(
    "changes_requested",
  );
  useEffect(() => {
    writeStoredJson(storageKey, checklist);
  }, [checklist, storageKey]);
  const rerender = useMutation({
    mutationFn: () => api.startRender(projectId),
    onSuccess: (next) => setJobId(next.job_id),
  });
  const submit = useMutation({
    mutationFn: () =>
      api.submitReview(projectId, { reviewer, comments, decision, checklist }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      navigate(`/projects/${projectId}/approval`);
    },
  });
  const allChecked = Object.values(checklist).every(Boolean);

  return (
    <div>
      <PageHeader
        eyebrow="Step 5 of 6 · Draft Review"
        title="Watch and review the complete draft"
        description="Technical validation is not human approval. Watch the entire local draft before completing the checklist."
        actions={
          <Button variant="secondary" onClick={() => rerender.mutate()}>
            <RefreshCw className="h-4 w-4" /> Render again
          </Button>
        }
      />
      {job.data && job.data.status !== "COMPLETED" ? (
        <JobProgress job={job.data} />
      ) : null}
      {draft.data ? (
        <div className="space-y-6">
          <Card className="overflow-hidden border-0 bg-video">
            <div className="aspect-video">
              <video
                src={api.mediaUrl(projectId)}
                controls
                preload="metadata"
                className="h-full w-full bg-black"
                aria-label="Rendered draft video"
              />
            </div>
          </Card>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            <Card>
              <CardContent>
                <p className="text-xs text-ink-muted">Duration</p>
                <strong>
                  {draft.data.metadata.duration_seconds.toFixed(3)} s
                </strong>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <p className="text-xs text-ink-muted">Output</p>
                <strong>
                  {draft.data.metadata.width} × {draft.data.metadata.height}
                </strong>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <p className="text-xs text-ink-muted">Renderer</p>
                <strong>{draft.data.renderer_used}</strong>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <p className="text-xs text-ink-muted">Sync state</p>
                <Badge
                  tone={
                    draft.data.sync_state === "verified" ? "success" : "warning"
                  }
                >
                  {draft.data.sync_state}
                </Badge>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <p className="text-xs text-ink-muted">Compliance</p>
                <Badge
                  tone={
                    draft.data.compliance_state.includes("SMOKE")
                      ? "warning"
                      : "success"
                  }
                >
                  {formatStatusLabel(draft.data.compliance_state)}
                </Badge>
              </CardContent>
            </Card>
          </div>
          <DurationMetricsPanel
            commonOverlap={draft.data.common_overlap_duration}
            eventCoverage={draft.data.total_event_coverage}
            maximumRenderable={draft.data.maximum_renderable_duration}
          />
          {project?.smoke_mode || draft.data.sync_state !== "verified" ? (
            <Alert tone="warning" title="Restricted technical draft">
              {project?.smoke_mode
                ? "Smoke mode is not compliant with the 60–180 second requirement. "
                : ""}
              {draft.data.sync_state !== "verified"
                ? "Synchronisation is unverified. "
                : ""}
              The review can record requested changes, but this draft cannot be
              approved.
            </Alert>
          ) : null}
          <Card>
            <CardHeader>
              <h2 className="text-lg font-bold">Human review record</h2>
              <p className="mt-1 text-sm text-ink-muted">
                Checklist progress is saved in this browser until submitted.
              </p>
            </CardHeader>
            <CardContent className="space-y-6">
              <ReviewChecklist values={checklist} onChange={setChecklist} />
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label htmlFor="reviewer">Reviewer name</Label>
                  <Input
                    id="reviewer"
                    value={reviewer}
                    onChange={(event) => setReviewer(event.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="decision">Decision</Label>
                  <Select
                    id="decision"
                    value={decision}
                    onChange={(event) =>
                      setDecision(event.target.value as typeof decision)
                    }
                  >
                    <option value="changes_requested">Changes requested</option>
                    <option
                      value="approved"
                      disabled={
                        !allChecked ||
                        project?.smoke_mode ||
                        draft.data.sync_state !== "verified"
                      }
                    >
                      Approved — all requirements verified
                    </option>
                  </Select>
                </div>
              </div>
              <div>
                <Label htmlFor="comments">Review comments</Label>
                <Textarea
                  id="comments"
                  value={comments}
                  onChange={(event) => setComments(event.target.value)}
                  placeholder="Record perceptual, privacy, sync, and editing observations."
                />
              </div>
              {submit.error ? (
                <Alert tone="danger" title="Review could not be recorded">
                  {submit.error.message}
                </Alert>
              ) : null}
              <div className="flex justify-end">
                <Button
                  size="lg"
                  disabled={!reviewer.trim() || submit.isPending}
                  onClick={() => submit.mutate()}
                >
                  <FileCheck2 className="h-5 w-5" /> Record Review{" "}
                  <ChevronRight className="h-5 w-5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}
      {!draft.data && !job.data ? (
        <Alert tone="info" title="No draft has been rendered">
          <Button className="mt-2" onClick={() => rerender.mutate()}>
            <Play className="h-4 w-4" /> Render draft
          </Button>
        </Alert>
      ) : null}
    </div>
  );
}
