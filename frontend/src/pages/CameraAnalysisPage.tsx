import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Camera,
  ChevronRight,
  FileWarning,
  RefreshCw,
  Video,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import { api } from "../api/client";
import type { PairScore } from "../api/types";
import { JobProgress } from "../components/JobProgress";
import { DurationMetricsPanel } from "../components/DurationMetricsPanel";
import { PageHeader } from "../components/PageHeader";
import { Alert } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader } from "../components/ui/card";
import { Progress } from "../components/ui/progress";
import { useCurrentProject } from "../context/ProjectContext";
import { useJob } from "../hooks/useJob";

const tone = (confidence: string) =>
  confidence === "high"
    ? "success"
    : confidence === "medium"
      ? "warning"
      : "danger";

function PairEvidence({ pair }: { pair: PairScore }) {
  return (
    <details className="rounded-lg border border-border bg-white p-4">
      <summary className="flex cursor-pointer list-none items-center gap-3">
        <Badge
          tone={
            pair.accepted ? "success" : pair.suggested ? "warning" : "danger"
          }
        >
          {pair.accepted
            ? "Accepted"
            : pair.suggested
              ? "Suggested for human verification"
              : "Rejected"}
        </Badge>
        <strong className="text-sm">
          {pair.camera_a} ↔ {pair.camera_b}
        </strong>
        <span className="ml-auto text-sm font-bold">
          {Math.round(pair.total_score * 100)}%
        </span>
      </summary>
      <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <span className="text-ink-muted">Audio correlation</span>
          <strong className="block">{pair.audio_correlation.toFixed(3)}</strong>
        </div>
        <div>
          <span className="text-ink-muted">Estimated offset</span>
          <strong className="block">
            {pair.estimated_offset_seconds?.toFixed(3) ?? "n/a"} s
          </strong>
        </div>
        <div>
          <span className="text-ink-muted">Offset stability</span>
          <strong className="block">{pair.offset_stability.toFixed(3)}</strong>
        </div>
        <div>
          <span className="text-ink-muted">Shared transients</span>
          <strong className="block">{pair.shared_transient_count}</strong>
        </div>
      </div>
      <p className="mt-3 text-sm leading-6 text-ink-muted">{pair.reason}</p>
    </details>
  );
}

export function CameraAnalysisPage() {
  const { projectId = "" } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: project } = useCurrentProject();
  const initialJob =
    (location.state as { jobId?: string } | null)?.jobId ??
    project?.latest_job_id;
  const [jobId, setJobId] = useState<string | null>(initialJob ?? null);
  const [manualIds, setManualIds] = useState<string[]>([]);
  const [manualMaster, setManualMaster] = useState("");
  const job = useJob(jobId);
  const complete = job.data?.status === "COMPLETED";
  const analysis = useQuery({
    queryKey: ["analysis", projectId],
    queryFn: () => api.getAnalysis(projectId),
    enabled: complete || !jobId,
    retry: false,
  });
  const rerun = useMutation({
    mutationFn: () => api.startAnalysis(projectId),
    onSuccess: (next) => {
      setJobId(next.job_id);
      queryClient.removeQueries({ queryKey: ["analysis", projectId] });
    },
  });
  const beginSync = useMutation({
    mutationFn: () => api.startSync(projectId),
    onSuccess: (next) =>
      navigate(`/projects/${projectId}/synchronisation`, {
        state: { jobId: next.job_id },
      }),
  });
  const data = analysis.data;
  useEffect(() => {
    if (!data) return;
    const initialIds = data.selected_camera_ids.length
      ? data.selected_camera_ids
      : data.suggested_camera_ids;
    setManualIds(initialIds);
    setManualMaster(
      data.master_camera ?? data.suggested_master_camera ?? initialIds[0] ?? "",
    );
  }, [data]);
  const excluded = useMemo(
    () => data?.videos.filter((item) => !item.usable) ?? [],
    [data],
  );
  const selected = new Set(manualIds);
  const saveSelection = useMutation({
    mutationFn: () =>
      api.selectCameras(
        projectId,
        manualIds,
        manualMaster,
        data?.grouping.state === "CAMERA_GROUP_LOW_CONFIDENCE",
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["analysis", projectId] }),
  });
  const continueToSync = async () => {
    await api.selectCameras(
      projectId,
      manualIds,
      manualMaster,
      data?.grouping.state === "CAMERA_GROUP_LOW_CONFIDENCE",
    );
    beginSync.mutate();
  };

  return (
    <div>
      <PageHeader
        eyebrow="Step 2 of 6 · Analysis"
        title="Camera analysis"
        description="Review exactly what the deterministic grouping stage inspected, selected, and rejected."
        actions={
          <Button
            variant="secondary"
            onClick={() => rerun.mutate()}
            disabled={rerun.isPending}
          >
            <RefreshCw className="h-4 w-4" /> Re-analyse
          </Button>
        }
      />
      {job.data && job.data.status !== "COMPLETED" ? (
        <JobProgress job={job.data} />
      ) : null}
      {data ? (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Card>
              <CardContent>
                <p className="text-sm text-ink-muted">Discovered</p>
                <p className="mt-1 text-3xl font-bold">{data.videos.length}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <p className="text-sm text-ink-muted">Eligible sources</p>
                <p className="mt-1 text-3xl font-bold">
                  {data.videos.filter((item) => item.usable).length}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <p className="text-sm text-ink-muted">Pairs analysed</p>
                <p className="mt-1 text-3xl font-bold">
                  {data.grouping.analysed_pair_count}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <p className="text-sm text-ink-muted">Group confidence</p>
                <div className="mt-2">
                  <Badge tone={tone(data.grouping.confidence)}>
                    {data.grouping.confidence.toUpperCase()}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>
          <DurationMetricsPanel
            commonOverlap={data.common_overlap_duration}
            eventCoverage={data.total_event_coverage}
            maximumRenderable={data.maximum_renderable_duration}
          />
          <Alert
            tone={data.selected_camera_ids.length >= 2 ? "success" : "warning"}
            title={data.grouping.state.replaceAll("_", " ")}
          >
            {data.grouping.reason}
          </Alert>
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold">Source inventory</h2>
                  <p className="mt-1 text-sm text-ink-muted">
                    Selected cameras are clearly marked; all source files remain
                    read-only.
                  </p>
                </div>
                <Badge tone="primary">
                  Master: {data.master_camera ?? "not selected"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
              {data.videos
                .filter((item) => item.usable)
                .map((video) => (
                  <article
                    key={video.relative_path}
                    className={`rounded-xl border p-4 ${selected.has(video.camera_id ?? "") ? "border-primary bg-primary-soft/40" : "border-border"}`}
                  >
                    <div className="flex items-start gap-3">
                      <span className="rounded-lg bg-subtle p-2 text-primary">
                        <Camera className="h-5 w-5" />
                      </span>
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <input
                            type="checkbox"
                            aria-label={`Select ${video.camera_id}`}
                            checked={selected.has(video.camera_id ?? "")}
                            onChange={(event) => {
                              const id = video.camera_id ?? "";
                              setManualIds((current) =>
                                event.target.checked
                                  ? [...new Set([...current, id])].slice(0, 4)
                                  : current.filter((item) => item !== id),
                              );
                              if (event.target.checked && !manualMaster) {
                                setManualMaster(id);
                              }
                            }}
                          />
                          <strong>{video.camera_id}</strong>
                          {selected.has(video.camera_id ?? "") ? (
                            <Badge tone="primary">Selected</Badge>
                          ) : null}
                          {video.camera_id === data.master_camera ? (
                            <Badge tone="success">Master</Badge>
                          ) : null}
                        </div>
                        <p
                          className="mt-1 truncate text-sm text-ink-muted"
                          title={video.relative_path}
                        >
                          {video.relative_path}
                        </p>
                      </div>
                    </div>
                    <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <dt className="text-ink-muted">Duration</dt>
                        <dd className="font-semibold">
                          {video.duration_seconds?.toFixed(2)} s
                        </dd>
                      </div>
                      <div>
                        <dt className="text-ink-muted">Frame</dt>
                        <dd className="font-semibold">
                          {video.width} × {video.height}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-ink-muted">Frame rate</dt>
                        <dd className="font-semibold">
                          {video.fps?.toFixed(2)} fps
                        </dd>
                      </div>
                      <div>
                        <dt className="text-ink-muted">Audio</dt>
                        <dd className="font-semibold">
                          {video.has_audio ? video.audio_codec : "None"}
                        </dd>
                      </div>
                    </dl>
                    {selected.has(video.camera_id ?? "") ? (
                      <label className="mt-3 flex items-center gap-2 text-xs font-semibold text-ink-muted">
                        <input
                          type="radio"
                          name="master-camera"
                          checked={manualMaster === video.camera_id}
                          onChange={() =>
                            setManualMaster(video.camera_id ?? "")
                          }
                        />
                        Use as master camera
                      </label>
                    ) : null}
                  </article>
                ))}
            </CardContent>
          </Card>
          {excluded.length ? (
            <Card>
              <CardHeader>
                <h2 className="flex items-center gap-2 text-lg font-bold">
                  <FileWarning className="h-5 w-5 text-warning" /> Excluded
                  files
                </h2>
              </CardHeader>
              <CardContent className="space-y-3">
                {excluded.map((video) => (
                  <div
                    key={video.relative_path}
                    className="flex flex-col gap-2 rounded-lg bg-subtle p-4 sm:flex-row sm:items-center"
                  >
                    <Video className="h-5 w-5 text-ink-faint" />
                    <span className="min-w-0 flex-1 truncate text-sm font-semibold">
                      {video.relative_path}
                    </span>
                    <Badge tone="warning">
                      {video.classification.replaceAll("_", " ")}
                    </Badge>
                    <span className="text-xs text-ink-muted">
                      {video.warnings[0]}
                    </span>
                  </div>
                ))}
              </CardContent>
            </Card>
          ) : null}
          <Card>
            <CardHeader>
              <h2 className="text-lg font-bold">Pair-analysis evidence</h2>
              <p className="mt-1 text-sm text-ink-muted">
                Scores combine audio correlation, offset stability, shared
                transients, timing, duration, and source confidence.
              </p>
            </CardHeader>
            <CardContent className="space-y-3">
              {data.grouping.pair_scores?.map((pair) => (
                <PairEvidence
                  key={`${pair.camera_a}-${pair.camera_b}`}
                  pair={pair}
                />
              ))}
            </CardContent>
          </Card>
          <div className="flex flex-col justify-end gap-3 sm:flex-row">
            <Button
              variant="secondary"
              disabled={
                manualIds.length < 2 || !manualMaster || saveSelection.isPending
              }
              onClick={() => saveSelection.mutate()}
            >
              Save Camera Selection
            </Button>
            <Button
              size="lg"
              disabled={manualIds.length < 2 || beginSync.isPending}
              onClick={() => void continueToSync()}
            >
              {data.grouping.state === "CAMERA_GROUP_LOW_CONFIDENCE"
                ? "Continue with Human Verification"
                : "Analyse Synchronisation"}{" "}
              <ChevronRight className="h-5 w-5" />
            </Button>
          </div>
        </div>
      ) : null}
      {!data && !job.data && analysis.isError ? (
        <Alert tone="warning" title="Analysis has not run">
          Return to Footage and select Analyse Footage.
        </Alert>
      ) : null}
      {data?.grouping.best_score != null ? (
        <div className="sr-only">
          <Progress
            value={data.grouping.best_score * 100}
            label="Best camera grouping score"
          />
        </div>
      ) : null}
    </div>
  );
}
