import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  ChevronRight,
  Clock3,
  RotateCcw,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import { api } from "../api/client";
import { JobProgress } from "../components/JobProgress";
import { DurationMetricsPanel } from "../components/DurationMetricsPanel";
import { PageHeader } from "../components/PageHeader";
import { WaveformPreview } from "../components/WaveformPreview";
import { Alert } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader } from "../components/ui/card";
import { Input, Label } from "../components/ui/form";
import { useCurrentProject } from "../context/ProjectContext";
import { useJob } from "../hooks/useJob";
import { formatStatusLabel } from "../lib/utils";

export function SynchronisationPage() {
  const { projectId = "" } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: project } = useCurrentProject();
  const initialJob =
    (location.state as { jobId?: string } | null)?.jobId ??
    (project?.current_step === 3 ? project.latest_job_id : null);
  const [jobId, setJobId] = useState<string | null>(initialJob ?? null);
  const job = useJob(jobId);
  const complete = job.data?.status === "COMPLETED";
  const report = useQuery({
    queryKey: ["sync", projectId],
    queryFn: () => api.getSync(projectId),
    enabled: complete || !jobId,
    retry: false,
  });
  const [timestamps, setTimestamps] = useState<Record<string, number>>({});
  const [riskAcknowledged, setRiskAcknowledged] = useState<
    Record<string, boolean>
  >({});
  const [rejectionReasons, setRejectionReasons] = useState<
    Record<string, string>
  >({});
  useEffect(() => {
    if (report.data) setTimestamps(report.data.clap_timestamps);
  }, [report.data]);
  const detect = useMutation({
    mutationFn: () => api.startSync(projectId),
    onSuccess: (next) => setJobId(next.job_id),
  });
  const confirm = useMutation({
    mutationFn: ({
      cameraId,
      timestamp,
      acknowledgeRisk,
    }: {
      cameraId: string;
      timestamp: number;
      acknowledgeRisk: boolean;
    }) => api.confirmSync(projectId, cameraId, timestamp, acknowledgeRisk),
    onSuccess: (data) => queryClient.setQueryData(["sync", projectId], data),
  });
  const reject = useMutation({
    mutationFn: ({
      cameraId,
      timestamp,
      reason,
    }: {
      cameraId: string;
      timestamp?: number;
      reason: string;
    }) => api.rejectSync(projectId, cameraId, timestamp, reason),
    onSuccess: (data) => queryClient.setQueryData(["sync", projectId], data),
  });
  const generate = useMutation({
    mutationFn: () => api.startEdl(projectId),
    onSuccess: (next) =>
      navigate(`/projects/${projectId}/editing-plan`, {
        state: { jobId: next.job_id },
      }),
  });
  const masterTime = report.data
    ? timestamps[report.data.master_camera]
    : undefined;
  const confirmations = report.data?.manual_confirmations ?? {};
  const allVerified = report.data?.acceptance_status === "verified";
  const cards = useMemo(
    () => report.data?.camera_analyses ?? [],
    [report.data],
  );

  return (
    <div>
      <PageHeader
        eyebrow="Step 3 of 6 · Synchronisation"
        title="Verify synchronisation cues"
        description="The assistant ranks shared local-audio transients. Only a human confirmation can mark a cue as a verified clap."
        actions={
          <Button variant="secondary" onClick={() => detect.mutate()}>
            <RotateCcw className="h-4 w-4" /> Detect again
          </Button>
        }
      />
      {job.data && job.data.status !== "COMPLETED" ? (
        <JobProgress job={job.data} />
      ) : null}
      {report.data ? (
        <div className="space-y-6">
          <Alert
            tone={allVerified ? "success" : "warning"}
            title={
              allVerified
                ? "Manual clap synchronisation verified"
                : "Human verification required"
            }
          >
            {report.data.cue_description}
            <span className="mt-2 block font-semibold">
              Grouping confidence is separate from clap verification.
            </span>
          </Alert>
          <DurationMetricsPanel
            commonOverlap={
              report.data.duration_metrics?.common_overlap_duration ??
              report.data.sync_sanity?.common_usable_duration_seconds
            }
            eventCoverage={report.data.duration_metrics?.total_event_coverage}
            maximumRenderable={
              report.data.duration_metrics?.maximum_renderable_duration
            }
          />
          <p className="text-xs leading-5 text-ink-muted">
            Common overlap is shown here only as synchronization evidence. Total
            event coverage and maximum renderable duration govern editing.
          </p>
          {confirm.isError ? (
            <Alert tone="danger" title="Cue confirmation needs attention">
              {confirm.error.message}
            </Alert>
          ) : null}
          {reject.isError ? (
            <Alert tone="danger" title="Cue rejection needs attention">
              {reject.error.message}
            </Alert>
          ) : null}
          {report.data.sync_sanity?.warnings.length ? (
            <Alert tone="warning" title="Synchronisation overlap warning">
              {report.data.sync_sanity.warnings.join(" ")}
            </Alert>
          ) : null}
          <div className="grid gap-5 xl:grid-cols-2">
            {cards.map((item) => {
              const timestamp =
                timestamps[item.camera_id] ??
                item.selected_timestamp_seconds ??
                item.candidates[0]?.timestamp_seconds ??
                0;
              const offset = masterTime == null ? null : timestamp - masterTime;
              const largeOffset = offset != null && Math.abs(offset) > 10;
              const verified = Boolean(confirmations[item.camera_id]);
              return (
                <Card key={item.camera_id}>
                  <CardHeader>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="text-lg font-bold">{item.camera_id}</h2>
                      {item.camera_id === report.data?.master_camera ? (
                        <Badge tone="primary">Master</Badge>
                      ) : null}
                      <Badge
                        tone={
                          verified
                            ? "success"
                            : item.confidence >= 0.65
                              ? "warning"
                              : "danger"
                        }
                      >
                        {verified
                          ? "Manually verified"
                          : formatStatusLabel(item.state)}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-3 gap-3 text-sm">
                      <div>
                        <span className="text-ink-muted">Confidence</span>
                        <strong className="block text-lg">
                          {Math.round(item.confidence * 100)}%
                        </strong>
                      </div>
                      <div>
                        <span className="text-ink-muted">Estimated offset</span>
                        <strong className="block text-lg">
                          {offset == null
                            ? "n/a"
                            : `${offset >= 0 ? "+" : ""}${offset.toFixed(3)} s`}
                        </strong>
                      </div>
                      <div>
                        <span className="text-ink-muted">Cue type</span>
                        <strong className="block text-sm">
                          {formatStatusLabel(item.state)}
                        </strong>
                      </div>
                    </div>
                    {item.candidates.length ? (
                      <div className="flex flex-wrap gap-2">
                        {item.candidates.map((candidate) => (
                          <button
                            type="button"
                            key={`${candidate.timestamp_seconds}-${candidate.cue_type}`}
                            className="rounded-lg border border-border bg-subtle px-3 py-2 text-left text-xs hover:border-primary"
                            onClick={() =>
                              setTimestamps((current) => ({
                                ...current,
                                [item.camera_id]: candidate.timestamp_seconds,
                              }))
                            }
                          >
                            <strong className="block">
                              {candidate.timestamp_seconds.toFixed(3)} s
                            </strong>
                            {formatStatusLabel(candidate.cue_type)} ·{" "}
                            {Math.round(candidate.confidence * 100)}%
                          </button>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-danger">
                        No reliable timestamp was invented for this camera.
                      </p>
                    )}
                    {timestamp > 0 ? (
                      <WaveformPreview
                        mediaUrl={api.cueUrl(projectId, item.camera_id)}
                        timestamp={timestamp}
                      />
                    ) : null}
                    <div>
                      <Label htmlFor={`time-${item.camera_id}`}>
                        Confirmed timestamp (seconds)
                      </Label>
                      <div className="flex gap-2">
                        <Input
                          id={`time-${item.camera_id}`}
                          type="number"
                          min="0"
                          step="0.001"
                          value={timestamp || ""}
                          onChange={(event) =>
                            setTimestamps((current) => ({
                              ...current,
                              [item.camera_id]: Number(event.target.value),
                            }))
                          }
                        />
                        <Button
                          type="button"
                          onClick={() =>
                            confirm.mutate({
                              cameraId: item.camera_id,
                              timestamp,
                              acknowledgeRisk: Boolean(
                                riskAcknowledged[item.camera_id],
                              ),
                            })
                          }
                          disabled={
                            !Number.isFinite(timestamp) || confirm.isPending
                          }
                        >
                          <CheckCircle2 className="h-4 w-4" /> Confirm Cue
                        </Button>
                      </div>
                      {largeOffset ? (
                        <label className="mt-3 flex items-start gap-2 rounded-lg bg-warning-soft p-3 text-xs leading-5 text-warning">
                          <input
                            type="checkbox"
                            checked={Boolean(riskAcknowledged[item.camera_id])}
                            onChange={(event) =>
                              setRiskAcknowledged((current) => ({
                                ...current,
                                [item.camera_id]: event.target.checked,
                              }))
                            }
                          />
                          I verified that this is the same cue and acknowledge
                          that the large offset may reduce usable overlap.
                        </label>
                      ) : null}
                    </div>
                    <div>
                      <Label htmlFor={`reject-reason-${item.camera_id}`}>
                        Reason for rejecting candidate
                      </Label>
                      <Input
                        id={`reject-reason-${item.camera_id}`}
                        value={rejectionReasons[item.camera_id] ?? ""}
                        placeholder="Explain why this cue is unsuitable"
                        onChange={(event) =>
                          setRejectionReasons((current) => ({
                            ...current,
                            [item.camera_id]: event.target.value,
                          }))
                        }
                      />
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      className="text-danger"
                      disabled={
                        !rejectionReasons[item.camera_id]?.trim() ||
                        reject.isPending
                      }
                      onClick={() =>
                        reject.mutate({
                          cameraId: item.camera_id,
                          timestamp,
                          reason: (
                            rejectionReasons[item.camera_id] ?? ""
                          ).trim(),
                        })
                      }
                    >
                      <XCircle className="h-4 w-4" /> Reject Candidate
                    </Button>
                    {item.warnings.map((warning) => (
                      <p
                        key={warning}
                        className="text-xs leading-5 text-warning"
                      >
                        {warning}
                      </p>
                    ))}
                  </CardContent>
                </Card>
              );
            })}
          </div>
          {report.data.pairwise_alignment?.length ? (
            <Card>
              <CardHeader>
                <h2 className="text-lg font-bold">
                  Multi-window offset diagnostics
                </h2>
                <p className="mt-1 text-sm text-ink-muted">
                  Alternatives are ranked using audio correlation, consistency
                  across early/middle/late windows, and preserved overlap. They
                  are suggestions, not verified claps.
                </p>
              </CardHeader>
              <CardContent className="space-y-3">
                {report.data.pairwise_alignment.map((pair) => (
                  <details
                    key={`${pair.camera_a}-${pair.camera_b}`}
                    className="rounded-lg border border-border p-4"
                  >
                    <summary className="cursor-pointer font-semibold">
                      {pair.camera_a} to {pair.camera_b} -{" "}
                      {formatStatusLabel(pair.state)}
                    </summary>
                    <p className="mt-2 text-sm text-ink-muted">{pair.reason}</p>
                    <div className="mt-3 space-y-2">
                      {pair.alternatives.map((candidate) => (
                        <div
                          key={candidate.offset_seconds}
                          className="grid gap-2 rounded-lg bg-subtle p-3 text-xs sm:grid-cols-4"
                        >
                          <strong>
                            {candidate.offset_seconds >= 0 ? "+" : ""}
                            {candidate.offset_seconds.toFixed(3)} s
                          </strong>
                          <span>
                            Correlation {candidate.audio_correlation.toFixed(3)}
                          </span>
                          <span>
                            Stability {candidate.offset_stability.toFixed(3)}
                          </span>
                          <span>
                            Overlap {candidate.overlap_seconds.toFixed(2)} s
                          </span>
                        </div>
                      ))}
                    </div>
                  </details>
                ))}
              </CardContent>
            </Card>
          ) : null}
          <Card>
            <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center">
              <Clock3 className="h-7 w-7 text-primary" />
              <div className="flex-1">
                <h2 className="font-bold">
                  Acceptance threshold: ±{report.data.verification_threshold_ms}{" "}
                  ms
                </h2>
                <p className="text-sm text-ink-muted">
                  Automatic offsets remain suggestions until every camera cue is
                  confirmed by a reviewer.
                </p>
              </div>
              <Badge tone={allVerified ? "success" : "warning"}>
                {formatStatusLabel(report.data.acceptance_status)}
              </Badge>
            </CardContent>
          </Card>
          <div className="flex justify-end">
            <Button
              size="lg"
              onClick={() => generate.mutate()}
              disabled={
                generate.isPending ||
                (!allVerified && !project?.smoke_mode) ||
                (project?.smoke_mode &&
                  cards.some(
                    (item) =>
                      timestamps[item.camera_id] == null &&
                      item.selected_timestamp_seconds == null,
                  ))
              }
            >
              Generate Editing Plan <ChevronRight className="h-5 w-5" />
            </Button>
          </div>
        </div>
      ) : null}
      {!report.data && !job.data ? (
        <Alert tone="info" title="No cue analysis yet">
          <Button className="mt-2" onClick={() => detect.mutate()}>
            Detect synchronisation cues
          </Button>
        </Alert>
      ) : null}
    </div>
  );
}
