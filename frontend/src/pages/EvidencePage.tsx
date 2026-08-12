import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Check,
  Clipboard,
  Download,
  FileJson2,
  FolderSearch,
} from "lucide-react";
import { useState } from "react";
import { useParams } from "react-router-dom";

import { api } from "../api/client";
import type { EvidenceItem } from "../api/types";
import { formatStatusLabel } from "../lib/utils";
import { PageHeader } from "../components/PageHeader";
import { DurationMetricsPanel } from "../components/DurationMetricsPanel";
import { QueryState } from "../components/QueryState";
import { Alert } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";

function EvidenceCard({
  projectId,
  item,
}: {
  projectId: string;
  item: EvidenceItem;
}) {
  const [copyState, setCopyState] = useState<"idle" | "success" | "error">(
    "idle",
  );
  const payload = useMutation({
    mutationFn: () => api.getEvidence(projectId, item.id),
  });
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(item.path);
      setCopyState("success");
      window.setTimeout(() => setCopyState("idle"), 1500);
    } catch {
      setCopyState("error");
    }
  };
  return (
    <Card>
      <CardContent className="space-y-4">
        <div className="flex items-start gap-3">
          <span className="rounded-lg bg-primary-soft p-2 text-primary">
            <FileJson2 className="h-5 w-5" />
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap gap-2">
              <h2 className="font-bold">{item.label}</h2>
              <Badge tone={item.exists ? "success" : "danger"}>
                {item.exists ? "Available" : "Missing"}
              </Badge>
            </div>
            <p
              className="mt-1 truncate text-xs text-ink-muted"
              title={item.path}
            >
              {item.path}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => payload.mutate()}
            disabled={!item.exists}
          >
            Expand JSON
          </Button>
          <Button variant="ghost" size="sm" onClick={copy}>
            {copyState === "success" ? (
              <Check className="h-4 w-4" />
            ) : (
              <Clipboard className="h-4 w-4" />
            )}{" "}
            Copy path
          </Button>
          {item.exists ? (
            <Button asChild variant="ghost" size="sm">
              <a href={api.downloadUrl(projectId, item.id)} download>
                <Download className="h-4 w-4" /> Download
              </a>
            </Button>
          ) : (
            <Button variant="ghost" size="sm" disabled>
              <Download className="h-4 w-4" /> Download
            </Button>
          )}
        </div>
        <p className="text-xs text-ink-muted" aria-live="polite">
          {copyState === "success"
            ? "Path copied to clipboard."
            : copyState === "error"
              ? "Path could not be copied. Select it manually above."
              : ""}
        </p>
        {payload.data ? (
          <pre className="max-h-96 overflow-auto rounded-lg bg-video p-4 text-xs leading-5 text-slate-200">
            {JSON.stringify(payload.data, null, 2)}
          </pre>
        ) : null}
        {payload.error ? (
          <Alert tone="danger" title="Evidence could not be opened">
            {payload.error.message}
          </Alert>
        ) : null}
      </CardContent>
    </Card>
  );
}

export function EvidencePage() {
  const { projectId = "" } = useParams();
  const query = useQuery({
    queryKey: ["evidence", projectId],
    queryFn: () => api.listEvidence(projectId),
  });
  const analysis = useQuery({
    queryKey: ["analysis", projectId],
    queryFn: () => api.getAnalysis(projectId),
    retry: false,
  });
  const grouped =
    query.data?.reduce<Record<string, EvidenceItem[]>>((result, item) => {
      (result[item.category] ??= []).push(item);
      return result;
    }, {}) ?? {};
  return (
    <div>
      <PageHeader
        eyebrow="Project evidence"
        title="Evidence and provenance"
        description="Inspect the local inventory, grouping evidence, synchronisation report, editing decisions, render validation, and human approval record."
      />
      <Alert tone="info" title="Transparent local processing" className="mb-6">
        Evidence contains technical metadata, decisions, reasons, warnings,
        checksums, and local paths. It contains no face, identity, or emotion
        analysis.
      </Alert>
      <QueryState
        isLoading={query.isLoading}
        error={query.error}
        loadingTitle="Loading project evidence"
        errorTitle="Evidence inventory could not be loaded"
        onRetry={() => void query.refetch()}
      />
      {analysis.data ? (
        <div className="mb-6">
          <DurationMetricsPanel
            commonOverlap={analysis.data.common_overlap_duration}
            eventCoverage={analysis.data.total_event_coverage}
            maximumRenderable={analysis.data.maximum_renderable_duration}
          />
        </div>
      ) : null}
      {Object.keys(grouped).length ? (
        <div className="space-y-8">
          {Object.entries(grouped).map(([category, items]) => (
            <section key={category}>
              <h2 className="mb-3 flex items-center gap-2 text-lg font-bold capitalize">
                <FolderSearch className="h-5 w-5 text-primary" />
                {formatStatusLabel(category)}
              </h2>
              <div className="grid gap-4 xl:grid-cols-2">
                {items.map((item) => (
                  <EvidenceCard
                    key={item.id}
                    projectId={projectId}
                    item={item}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : !query.isLoading && !query.error ? (
        <Alert tone="warning" title="No evidence registered">
          Complete analysis to generate the first evidence records.
        </Alert>
      ) : null}
    </div>
  );
}
