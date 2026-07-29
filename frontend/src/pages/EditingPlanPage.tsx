import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  ChevronRight,
  RefreshCw,
  Save,
  WandSparkles,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import { api } from "../api/client";
import type { EDL, EDLSegment } from "../api/types";
import { EditingTimeline } from "../components/EditingTimeline";
import { DurationMetricsPanel } from "../components/DurationMetricsPanel";
import { JobProgress } from "../components/JobProgress";
import { PageHeader } from "../components/PageHeader";
import { Alert } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader } from "../components/ui/card";
import { Input, Label, Select, Textarea } from "../components/ui/form";
import { useCurrentProject } from "../context/ProjectContext";
import { useJob } from "../hooks/useJob";

function localErrors(edl: EDL | null): string[] {
  if (!edl) return [];
  const errors: string[] = [];
  edl.timeline.forEach((segment, index) => {
    if (segment.end <= segment.start)
      errors.push(`${segment.id}: end must be after start.`);
    if (!segment.reason.trim())
      errors.push(`${segment.id}: reason is required.`);
    const previous = edl.timeline[index - 1];
    if (previous && Math.abs(previous.end - segment.start) > 0.001)
      errors.push(`${previous.id} and ${segment.id} must be contiguous.`);
  });
  const switches = edl.timeline
    .slice(1)
    .filter((item, index) => item.camera !== edl.timeline[index].camera).length;
  if (switches < 3) errors.push("At least three camera switches are required.");
  if (new Set(edl.timeline.map((item) => item.camera)).size < 2)
    errors.push("At least two cameras are required.");
  return errors;
}

export function EditingPlanPage() {
  const { projectId = "" } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: project } = useCurrentProject();
  const initialJob =
    (location.state as { jobId?: string } | null)?.jobId ??
    (project?.current_step === 4 ? project.latest_job_id : null);
  const [jobId, setJobId] = useState<string | null>(initialJob ?? null);
  const job = useJob(jobId);
  const complete = job.data?.status === "COMPLETED";
  const query = useQuery({
    queryKey: ["edl", projectId],
    queryFn: () => api.getEdl(projectId),
    enabled: complete || !jobId,
    retry: false,
  });
  const analysis = useQuery({
    queryKey: ["analysis", projectId],
    queryFn: () => api.getAnalysis(projectId),
    retry: false,
  });
  const [draft, setDraft] = useState<EDL | null>(null);
  useEffect(() => {
    if (query.data) setDraft(query.data);
  }, [query.data]);
  const errors = useMemo(() => localErrors(draft), [draft]);
  const regenerate = useMutation({
    mutationFn: () => api.startEdl(projectId),
    onSuccess: (next) => setJobId(next.job_id),
  });
  const save = useMutation({
    mutationFn: async () => {
      if (!draft) throw new Error("No EDL loaded");
      await api.updateEdl(projectId, draft);
      return api.validateEdl(projectId);
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["edl", projectId] }),
  });
  const render = useMutation({
    mutationFn: async () => {
      if (!draft || errors.length)
        throw new Error("Resolve editing plan errors before rendering.");
      await api.updateEdl(projectId, draft);
      await api.validateEdl(projectId);
      return api.startRender(projectId);
    },
    onSuccess: (next) =>
      navigate(`/projects/${projectId}/draft-review`, {
        state: { jobId: next.job_id },
      }),
  });
  const cameras = analysis.data?.videos
    .filter((item) => item.usable)
    .map((item) => item.camera_id)
    .filter((value): value is string => Boolean(value)) ?? [
    ...new Set(draft?.timeline.map((item) => item.camera) ?? []),
  ];
  const update = (index: number, changes: Partial<EDLSegment>) =>
    setDraft((current) =>
      current
        ? {
            ...current,
            timeline: current.timeline.map((item, itemIndex) =>
              itemIndex === index ? { ...item, ...changes } : item,
            ),
          }
        : current,
    );

  return (
    <div>
      <PageHeader
        eyebrow="Step 4 of 6 · Editing Plan"
        title="Review the deterministic editing plan"
        description="Adjust only camera choices, timing, reasons, and supported transitions. This is a guided plan—not a full professional editor."
        actions={
          <Button variant="secondary" onClick={() => regenerate.mutate()}>
            <RefreshCw className="h-4 w-4" /> Regenerate
          </Button>
        }
      />
      {job.data && job.data.status !== "COMPLETED" ? (
        <JobProgress job={job.data} />
      ) : null}
      {draft ? (
        <div className="space-y-6">
          <Alert tone="info" title="Explainable rule-based automation">
            Every proposed cut includes a human-readable reason. This
            deterministic rotation is not machine learning.
          </Alert>
          <DurationMetricsPanel
            commonOverlap={draft.common_overlap_duration}
            eventCoverage={draft.total_event_coverage}
            maximumRenderable={draft.maximum_renderable_duration}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <Card>
              <CardContent>
                <p className="text-sm text-ink-muted">Target Duration</p>
                <p className="mt-1 text-2xl font-bold">
                  {project?.duration_seconds.toFixed(2) ?? "n/a"} s
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <p className="text-sm text-ink-muted">
                  Maximum Renderable Duration
                </p>
                <p className="mt-1 text-2xl font-bold">
                  {draft.maximum_renderable_duration?.toFixed(2) ?? "n/a"} s
                </p>
              </CardContent>
            </Card>
          </div>
          {project &&
          draft.maximum_renderable_duration != null &&
          project.duration_seconds > draft.maximum_renderable_duration ? (
            <Alert tone="danger" title="Target exceeds renderable coverage">
              Reduce the target duration or revise the selected synchronized
              camera group. Common overlap is not used as this limit.
            </Alert>
          ) : null}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold">Simplified timeline</h2>
                  <p className="mt-1 text-sm text-ink-muted">
                    Colour, camera labels, and icons identify each segment.
                  </p>
                </div>
                <Badge tone={errors.length ? "danger" : "success"}>
                  {errors.length
                    ? `${errors.length} local issue${errors.length === 1 ? "" : "s"}`
                    : "Locally valid"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <EditingTimeline segments={draft.timeline} />
            </CardContent>
          </Card>
          {errors.length ? (
            <Alert tone="danger" title="Plan needs correction">
              <ul className="list-disc pl-5">
                {errors.map((error) => (
                  <li key={error}>{error}</li>
                ))}
              </ul>
            </Alert>
          ) : null}
          <div className="space-y-4">
            {draft.timeline.map((segment, index) => (
              <Card key={segment.id}>
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-soft text-sm font-bold text-primary">
                      {index + 1}
                    </span>
                    <div>
                      <h2 className="font-bold">{segment.id}</h2>
                      <p className="text-xs text-ink-muted">
                        {(segment.end - segment.start).toFixed(2)} second shot
                      </p>
                    </div>
                    {segment.overlay ? (
                      <Badge tone="primary" className="ml-auto">
                        {segment.overlay.type.replaceAll("_", " ")}:{" "}
                        {segment.overlay.text}
                      </Badge>
                    ) : null}
                  </div>
                </CardHeader>
                <CardContent className="grid gap-4 lg:grid-cols-[180px_120px_120px_180px_1fr]">
                  <div>
                    <Label htmlFor={`camera-${segment.id}`}>Camera</Label>
                    <Select
                      id={`camera-${segment.id}`}
                      value={segment.camera}
                      onChange={(event) =>
                        update(index, { camera: event.target.value })
                      }
                    >
                      {cameras.map((camera) => (
                        <option key={camera}>{camera}</option>
                      ))}
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor={`start-${segment.id}`}>Start</Label>
                    <Input
                      id={`start-${segment.id}`}
                      type="number"
                      step="0.001"
                      value={segment.start}
                      onChange={(event) =>
                        update(index, { start: Number(event.target.value) })
                      }
                    />
                  </div>
                  <div>
                    <Label htmlFor={`end-${segment.id}`}>End</Label>
                    <Input
                      id={`end-${segment.id}`}
                      type="number"
                      step="0.001"
                      value={segment.end}
                      onChange={(event) =>
                        update(index, { end: Number(event.target.value) })
                      }
                    />
                  </div>
                  <div>
                    <Label htmlFor={`action-${segment.id}`}>Transition</Label>
                    <Select
                      id={`action-${segment.id}`}
                      value={segment.action}
                      onChange={(event) =>
                        update(index, {
                          action: event.target.value as EDLSegment["action"],
                        })
                      }
                    >
                      <option value="cut">Cut</option>
                      <option value="fade_in">Fade in</option>
                      <option value="fade_out">Fade out</option>
                      <option value="fade_to_black">Fade to black</option>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor={`reason-${segment.id}`}>
                      Decision reason
                    </Label>
                    <Textarea
                      id={`reason-${segment.id}`}
                      value={segment.reason}
                      onChange={(event) =>
                        update(index, { reason: event.target.value })
                      }
                    />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          {save.error ? (
            <Alert tone="danger" title="Server validation failed">
              {save.error.message}
            </Alert>
          ) : null}
          {save.isSuccess ? (
            <Alert tone="success" title="Editing plan saved">
              <CheckCircle2 className="sr-only" />
              The existing EDL validator accepted every edit.
            </Alert>
          ) : null}
          <div className="flex flex-col justify-end gap-3 sm:flex-row">
            <Button
              variant="secondary"
              onClick={() => save.mutate()}
              disabled={errors.length > 0 || save.isPending}
            >
              <Save className="h-4 w-4" /> Save & Validate
            </Button>
            <Button
              size="lg"
              onClick={() => render.mutate()}
              disabled={errors.length > 0 || render.isPending}
            >
              <WandSparkles className="h-5 w-5" /> Render Draft{" "}
              <ChevronRight className="h-5 w-5" />
            </Button>
          </div>
        </div>
      ) : null}
      {!draft && !job.data && query.isError ? (
        <Alert tone="info" title="No editing plan yet">
          <Button className="mt-2" onClick={() => regenerate.mutate()}>
            Generate editing plan
          </Button>
        </Alert>
      ) : null}
    </div>
  );
}
