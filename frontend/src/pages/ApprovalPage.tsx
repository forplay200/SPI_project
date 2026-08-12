import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Ban,
  CheckCircle2,
  ClipboardCheck,
  FileKey2,
  LockKeyhole,
} from "lucide-react";
import { useParams } from "react-router-dom";

import { api } from "../api/client";
import { formatStatusLabel } from "../lib/utils";
import { PageHeader } from "../components/PageHeader";
import { Alert } from "../components/ui/alert";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader } from "../components/ui/card";

export function ApprovalPage() {
  const { projectId = "" } = useParams();
  const queryClient = useQueryClient();
  const eligibility = useQuery({
    queryKey: ["approval", projectId],
    queryFn: () => api.getApproval(projectId),
  });
  const approve = useMutation({
    mutationFn: () => api.approve(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approval", projectId] });
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    },
  });
  const data = eligibility.data;
  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        eyebrow="Step 6 of 6 · Approval"
        title="Final approval"
        description="Approval copies the exact reviewed bytes. It never edits, modifies, or rerenders the video."
      />
      {data ? (
        <div className="space-y-6">
          <Alert
            tone={data.eligible ? "success" : "warning"}
            title={
              data.eligible ? "Ready for final approval" : "Approval is blocked"
            }
          >
            {data.eligible
              ? "All automated controls and the human review record permit exact-byte promotion."
              : "Resolve every blocker below. The approval action remains disabled."}
          </Alert>
          <div className="grid gap-4 sm:grid-cols-3">
            <Card>
              <CardContent>
                <p className="text-sm text-ink-muted">Review status</p>
                <p className="mt-2 font-bold">
                  {formatStatusLabel(data.review_status)}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <p className="text-sm text-ink-muted">Sync status</p>
                <p className="mt-2 font-bold">
                  {formatStatusLabel(data.sync_status)}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <p className="text-sm text-ink-muted">Compliance</p>
                <p className="mt-2 font-bold">
                  {formatStatusLabel(data.compliance_status)}
                </p>
              </CardContent>
            </Card>
          </div>
          <Card>
            <CardHeader>
              <h2 className="flex items-center gap-2 text-lg font-bold">
                <LockKeyhole className="h-5 w-5 text-primary" /> Approval
                blockers
              </h2>
            </CardHeader>
            <CardContent>
              {data.blockers.length ? (
                <ul className="space-y-3">
                  {data.blockers.map((blocker) => (
                    <li
                      key={blocker}
                      className="flex gap-3 rounded-lg bg-danger-soft p-3 text-sm text-red-900"
                    >
                      <Ban className="h-5 w-5 shrink-0 text-danger" />
                      {blocker}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="flex items-center gap-3 rounded-lg bg-success-soft p-4 text-success">
                  <CheckCircle2 className="h-5 w-5" /> No blockers remain.
                </p>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <h2 className="flex items-center gap-2 text-lg font-bold">
                <FileKey2 className="h-5 w-5 text-primary" /> Reviewed draft
                checksum
              </h2>
            </CardHeader>
            <CardContent>
              <code className="block break-all rounded-lg bg-subtle p-4 text-xs text-ink">
                {data.draft_sha256 ?? "No draft checksum available"}
              </code>
              <p className="mt-3 text-sm text-ink-muted">
                Promotion verifies this SHA-256 before and after copying. Any
                change requires a new review.
              </p>
            </CardContent>
          </Card>
          {approve.error ? (
            <Alert tone="danger" title="Approval failed">
              {approve.error.message}
            </Alert>
          ) : null}
          {approve.data ? (
            <Alert tone="success" title="Exact reviewed draft promoted">
              Final approval completed without rerendering. SHA-256:{" "}
              {String(approve.data.sha256)}
            </Alert>
          ) : null}
          <div className="flex justify-end">
            <Button
              size="lg"
              disabled={!data.eligible || approve.isPending}
              onClick={() => approve.mutate()}
            >
              <ClipboardCheck className="h-5 w-5" /> Approve Exact Reviewed
              Draft
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
