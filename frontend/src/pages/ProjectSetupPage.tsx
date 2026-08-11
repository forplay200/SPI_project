import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FolderOpen, Play, ShieldCheck, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useParams } from "react-router-dom";

import { api } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { Alert } from "../components/ui/alert";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader } from "../components/ui/card";
import { Input, Label, Select } from "../components/ui/form";
import {
  useCurrentProject,
  useProjectContext,
} from "../context/ProjectContext";

type FormValues = {
  title: string;
  input_folder: string;
  duration_seconds: number;
  resolution: "1280x720" | "1920x1080";
  mode: "draft" | "smoke";
  credits: string;
  credits_duration: number | "";
};

export function ProjectSetupPage() {
  const { projectId } = useParams();
  const { data: current } = useCurrentProject();
  const { setProjectId } = useProjectContext();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const folderInput = useRef<HTMLInputElement>(null);
  const [selectedFiles, setSelectedFiles] = useState(0);
  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    defaultValues: {
      title: "Kindergarten Graduation Ceremony",
      input_folder: "input",
      duration_seconds: 90,
      resolution: "1280x720",
      mode: "draft",
      credits: "Edited by the Project Team",
      credits_duration: "",
    },
  });

  useEffect(() => {
    if (current)
      reset({
        title: current.title,
        input_folder: current.input_folder,
        duration_seconds: current.duration_seconds,
        resolution: current.resolution,
        mode: current.smoke_mode ? "smoke" : "draft",
        credits: current.credits,
        credits_duration: current.credits_duration ?? "",
      });
  }, [current, reset]);

  const mode = watch("mode");
  const submit = useMutation({
    mutationFn: async (values: FormValues) => {
      const payload = {
        title: values.title,
        input_folder: values.input_folder,
        duration_seconds: Number(values.duration_seconds),
        resolution: values.resolution,
        draft_mode: true,
        smoke_mode: values.mode === "smoke",
        credits: values.credits,
        credits_duration:
          values.credits_duration === ""
            ? null
            : Number(values.credits_duration),
      };
      const project = projectId
        ? await api.updateProject(projectId, payload)
        : await api.createProject(payload);
      const job = await api.startAnalysis(project.id);
      return { project, job };
    },
    onSuccess: ({ project, job }) => {
      setProjectId(project.id);
      queryClient.setQueryData(["project", project.id], {
        ...project,
        latest_job_id: job.job_id,
      });
      navigate(`/projects/${project.id}/analysis`, {
        state: { jobId: job.job_id },
      });
    },
  });

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        eyebrow="Step 1 of 6 · Footage"
        title="Set up your local project"
        description="Choose the approved footage folder and output target. Analysis reads files locally and never uploads source media."
      />
      {submit.error ? (
        <Alert
          tone="danger"
          title="Project could not be started"
          className="mb-5"
        >
          {submit.error.message}
        </Alert>
      ) : null}
      <form
        onSubmit={handleSubmit((values) => submit.mutate(values))}
        className="grid gap-6 lg:grid-cols-[1fr_320px]"
      >
        <Card>
          <CardHeader>
            <h2 className="text-lg font-bold">Project details</h2>
            <p className="mt-1 text-sm text-ink-muted">
              These values become the generated project configuration.
            </p>
          </CardHeader>
          <CardContent className="space-y-5">
            <div>
              <Label htmlFor="title">Project title</Label>
              <Input
                id="title"
                {...register("title", { required: "Enter a project title" })}
              />
              {errors.title ? (
                <p className="mt-1 text-xs text-danger">
                  {errors.title.message}
                </p>
              ) : null}
            </div>
            <div>
              <Label htmlFor="input-folder">Input folder</Label>
              <div className="flex gap-2">
                <Input
                  id="input-folder"
                  {...register("input_folder", {
                    required: "Choose an input folder",
                  })}
                />
                <Button
                  type="button"
                  variant="secondary"
                  aria-label="Browse local folder"
                  onClick={() => folderInput.current?.click()}
                >
                  <FolderOpen className="h-4 w-4" /> Browse
                </Button>
              </div>
              <input
                ref={folderInput}
                type="file"
                className="sr-only"
                multiple
                {...({ webkitdirectory: "" } as object)}
                onChange={(event) =>
                  setSelectedFiles(event.target.files?.length ?? 0)
                }
              />
              <p className="mt-2 text-xs text-ink-muted">
                Use a workspace-relative folder such as <code>input</code>.{" "}
                {selectedFiles
                  ? `${selectedFiles} local files selected for visual confirmation; the backend still validates the folder path.`
                  : "The browser does not upload selected files."}
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <Label htmlFor="duration">Target duration (seconds)</Label>
                <Input
                  id="duration"
                  type="number"
                  min={mode === "smoke" ? 7 : 60}
                  max={180}
                  step={1}
                  {...register("duration_seconds", {
                    valueAsNumber: true,
                    min: mode === "smoke" ? 7 : 60,
                    max: 180,
                  })}
                />
              </div>
              <div>
                <Label htmlFor="resolution">Resolution</Label>
                <Select id="resolution" {...register("resolution")}>
                  <option value="1280x720">1280 × 720 (recommended)</option>
                  <option value="1920x1080">1920 × 1080</option>
                </Select>
              </div>
            </div>
            <fieldset>
              <legend className="mb-2 text-sm font-semibold">Draft mode</legend>
              <div className="grid gap-3 sm:grid-cols-2">
                <label
                  className={`rounded-xl border p-4 ${mode === "draft" ? "border-primary bg-primary-soft" : "border-border"}`}
                >
                  <input
                    type="radio"
                    value="draft"
                    className="mr-2"
                    {...register("mode")}
                  />
                  <strong>Compliant draft</strong>
                  <span className="mt-1 block text-xs text-ink-muted">
                    Requires 60–180 seconds and remains subject to human
                    approval.
                  </span>
                </label>
                <label
                  className={`rounded-xl border p-4 ${mode === "smoke" ? "border-warning bg-warning-soft" : "border-border"}`}
                >
                  <input
                    type="radio"
                    value="smoke"
                    className="mr-2"
                    {...register("mode")}
                  />
                  <strong>Smoke test</strong>
                  <span className="mt-1 block text-xs text-ink-muted">
                    Short technical output, clearly labelled and never
                    approval-eligible.
                  </span>
                </label>
              </div>
            </fieldset>
            <div className="grid gap-4 sm:grid-cols-[1fr_180px]">
              <div>
                <Label htmlFor="credits">Closing credit text</Label>
                <Input
                  id="credits"
                  {...register("credits", { required: true })}
                />
              </div>
              <div>
                <Label htmlFor="credits-duration">Credit duration</Label>
                <Input
                  id="credits-duration"
                  type="number"
                  min="0.1"
                  max="30"
                  step="0.1"
                  placeholder={mode === "smoke" ? "1" : "4"}
                  {...register("credits_duration")}
                />
              </div>
            </div>
          </CardContent>
        </Card>
        <div className="space-y-5">
          <Card>
            <CardContent className="space-y-4">
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-soft text-primary">
                <Sparkles className="h-5 w-5" />
              </span>
              <div>
                <h2 className="font-bold">What happens next</h2>
                <p className="mt-1 text-sm leading-6 text-ink-muted">
                  All eligible videos are probed, derived outputs are shown
                  separately, and every camera pair receives explainable
                  metadata and local-audio analysis.
                </p>
              </div>
            </CardContent>
          </Card>
          <Alert tone="info" title="Human control is preserved">
            Analysis proposes a camera group. It does not verify a clap, approve
            a draft, or publish anything.
          </Alert>
          <Button
            type="submit"
            size="lg"
            className="w-full"
            disabled={submit.isPending}
          >
            {submit.isPending ? (
              "Starting analysis…"
            ) : (
              <>
                <Play className="h-5 w-5" /> Analyse Footage
              </>
            )}
          </Button>
          <p className="flex gap-2 text-xs leading-5 text-ink-muted">
            <ShieldCheck className="h-4 w-4 shrink-0 text-success" /> Input
            footage remains read-only. Generated files stay inside this
            workspace.
          </p>
        </div>
      </form>
    </div>
  );
}
