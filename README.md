# AI-Assisted Multi-Camera Kindergarten Graduation Video Editing Pipeline

This repository implements a local, semi-automated, deterministic video-editing
prototype. Its Automatic Preparation Layer can discover likely camera sources,
suggest audio synchronization cues, and generate a rule-based JSON Editing
Decision List (EDL). Every generated camera choice remains explainable and
reviewable. The established manual EDL workflow is still available.

Despite the official project title, the implemented camera switching is rule-based.
It does not use machine learning and must not be described as doing so.

## Requirements

- Python 3.10 or newer
- MoviePy 2.x (primary renderer)
- FFmpeg and FFprobe available on `PATH` (probing and fallback rendering)
- Local, consented or simulated video files

Install Python dependencies in a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Install FFmpeg using your operating system's trusted package source, then confirm:

```powershell
ffmpeg -version
ffprobe -version
```

The pipeline makes no network calls. Keep real footage local and never commit it.

## One-command automatic workflow

From the repository root on Windows PowerShell:

```powershell
python -m src.main auto `
  --input input `
  --duration 90 `
  --title "Kindergarten Graduation Ceremony"
```

The command discovers and probes local videos, conservatively groups files that
share event-time filename evidence, analyses only the first 15 seconds of local
audio, generates configuration and an EDL, validates them through the existing
pipeline, and renders a draft only when safe. It never reviews, approves,
publishes, or uploads a video.

The equivalent one-line command is:

```powershell
python -m src.main auto --input input --duration 90 --title "Kindergarten Graduation Ceremony"
```

Generated files are written to:

- `config/generated_project.json`
- `config/generated_sync.json`
- `edl/generated_editing_decisions.json`
- `evidence/reports/video_discovery.json`
- `evidence/reports/sync_candidates.json`
- `evidence/reports/generated_edl.json`
- `evidence/reports/automatic_preparation.json`
- `output/draft/` only when rendering is permitted

Generated configuration and EDL files do not replace different existing content
unless `--overwrite` is supplied. User-authored `config/project.json`,
`config/sync.json`, and `edl/editing_decisions.json` remain untouched.

## Assisted preparation workflow

Prepare and validate suggestions without rendering:

```powershell
python -m src.main prepare `
  --input input `
  --duration 90 `
  --title "Kindergarten Graduation Ceremony"
```

The summary reports one of the explicit states `READY_FOR_DRAFT`,
`READY_FOR_SMOKE_ONLY`, `NEEDS_CAMERA_SELECTION`,
`NEEDS_SYNC_CONFIRMATION`, `INSUFFICIENT_COMMON_DURATION`, or `INVALID_INPUT`.
An automatically detected transient is never called a verified clap. Candidate
timestamps, prominence/correlation metrics, confidence, warnings, and
`requires_human_verification` are saved for review.

The individual preparation commands are:

```powershell
python -m src.main inspect --input input
python -m src.main detect-sync --input input
python -m src.main generate-edl `
  --config config/generated_project.json `
  --sync config/generated_sync.json `
  --duration 90
```

If a human identifies the deliberate clap, record each verified source timestamp
without hand-editing JSON:

```powershell
python -m src.main confirm-sync `
  --camera camera_01 `
  --timestamp 5.695
```

All selected cameras must be confirmed before the generated sync file changes to
the `manual_clap` / `verified` state.

## Smoke versus compliant output

The normal duration policy is 60–180 seconds. If approved source footage is too
short, the software reports the maximum honest synchronized duration and does not
loop, freeze, slow, duplicate, or pad footage.

A short local renderer test requires explicit non-acceptance mode:

```powershell
python -m src.main auto `
  --input input `
  --duration 18 `
  --title "Kindergarten Graduation Ceremony" `
  --allow-smoke
```

Smoke and unverified-sync filenames identify their limitations. These drafts stay
under `output/draft/`, are reported as not submission-ready, and the approval
module rejects them as final outputs.

## Project setup

1. Place two to four approved videos in `input/`.
2. Update `config/project.json` with camera IDs and relative paths.
3. Find the same visible or audible clap in every recording and enter each source
   timestamp in `config/sync.json`.
4. Edit `edl/editing_decisions.json` using master-timeline seconds.
5. Keep at least two cameras, three adjacent camera changes, one supported
   transition, and one overlay.

Relative camera paths are resolved from the repository root. Inputs inside
`output/` or `temp/` are rejected.

## Current approved demo-footage status

`config/project.json` maps the approved local files
`input/video_20260619_151529.mp4` and
`input/VID_20260619_151529.mp4` to stable IDs `camera_wide` and
`camera_close`. The originals remain ignored by Git and are treated as
read-only.

No deliberate clap could be confirmed from sampled frames and audio
visualisations. The 5.695-second values in `config/sync.json` identify a
measured shared speech transient for smoke testing only; the evidence explicitly
marks it as unconfirmed and requiring manual clap review.

Every approved source is shorter than 26 seconds. The selected synchronized pair
has approximately 22.985 seconds of common usable footage, so it cannot produce
a compliant 60-second draft without repetition, time stretching, fabricated
offsets, or excessive title/credit padding. Those workarounds are intentionally
not used. `config/smoke_project.json` and
`edl/smoke_editing_decisions.json` provide an honest 18-second renderer test:

```powershell
python -m src.main render `
  --config config/smoke_project.json `
  --sync config/sync.json `
  --edl edl/smoke_editing_decisions.json
```

## Commands

The commands below are the preserved expert/manual workflow. They remain useful
when a human has selected camera files, verified clap timestamps, and authored or
reviewed the EDL.

Check local dependencies:

```powershell
python -m src.main preflight
```

Validate inputs, probe media, calculate offsets, validate the EDL, and print the
renderer-neutral plan:

```powershell
python -m src.main validate
```

Render a temporary MP4, probe and validate it, then atomically promote it to
`output/draft/`:

```powershell
python -m src.main render
```

MoviePy is used first by default. If it fails for a renderer-specific reason and
fallback is enabled, FFmpeg is activated visibly and the reason and command record
are saved under `evidence/`.

Create a human review checklist:

```powershell
python -m src.main review-template `
  --draft output/draft/kindergarten-graduation-demo_draft.mp4
```

Watch the entire draft and change every verified checklist item to `true`. Record a
decision:

```powershell
python -m src.main review `
  --project kindergarten-graduation-demo `
  --draft output/draft/kindergarten-graduation-demo_draft.mp4 `
  --reviewer "Reviewer Name" `
  --decision approved `
  --comments "Complete manual playback review performed." `
  --checklist evidence/approvals/review_checklist.json
```

Promote only the unchanged approved bytes:

```powershell
python -m src.main approve `
  --draft output/draft/kindergarten-graduation-demo_draft.mp4 `
  --review-record evidence/approvals/review_record.json
```

If the draft changes after review, approval is rejected because its SHA-256 no
longer matches.

## Configuration

`config/project.json` defines:

- project name and explicit master camera;
- primary renderer and whether FFmpeg fallback is allowed;
- 1280×720, 30 fps output defaults and codecs;
- opening title and closing credit text/durations;
- two to four local camera IDs and paths;
- a configurable duration policy.

The default final-output policy is 60–180 seconds and includes the title and
credits. The PRD/architecture also contain a narrower 60–80 second statement. If
the lecturer confirms that narrower maximum, set `duration_policy.max_seconds` to
`80`; no code change is required.

`config/sync.json` uses:

```text
offset(camera) = clap_time(camera) - clap_time(master)
source_time = master_time + offset(camera)
```

Offsets are constant; this prototype does not correct clock drift.

The supplied academic footage currently uses a measured shared audio landmark
rather than a confirmed clap. `cue_type` and `acceptance_status` preserve that
limitation in evidence. It is suitable for local smoke testing, but does not
satisfy the manual-clap acceptance criterion until a human confirms an audible
clap (or replacement footage with a deliberate clap is supplied).

## EDL format

Each timeline item requires `id`, `start`, `end`, `camera`, `reason`, and `action`.
Supported actions are `cut`, `fade_in`, `fade_out`, and `fade_to_black`. Segments
must be chronological, contiguous, and non-overlapping.

An optional overlay has type `lower_third`, `label`, or `subtitle`; non-empty
`text`; optional master-timeline `start` and `end`; and position `top`, `center`,
or `bottom`. Overlay times must remain inside their segment.

## Evidence and output safety

- Preflight evidence records metadata, synchronization-cue offsets and status,
  decision reasons, switch count, and the requested backend.
- Render evidence records actual duration and streams, runtime, warnings, backend
  actually used, fallback reason, and output SHA-256.
- Incomplete outputs remain in `temp/` and are removed on failure.
- Rendering never writes directly to `output/final/`.
- Human review records the reviewer, UTC date, comments, decision, checklist, and
  exact draft SHA-256.

## Tests

Run all tests:

```powershell
python -m pytest -q
```

The test suite includes deterministic unit tests and FFmpeg/MoviePy integration
tests. Media-dependent tests skip with an explicit reason if the executable or
package is unavailable.

Run static checks:

```powershell
python -m ruff check src tests
python -m ruff format --check src tests
```

## Privacy, ethics, and limitations

- Use simulated footage unless written permission covers recording, editing,
  processing, and intended distribution.
- Faces, voices, names, uniforms, and locations may identify children under
  Malaysia's PDPA context; this software does not identify or analyse people.
- There is no face recognition, emotion recognition, biometric analysis, cloud
  upload, telemetry, autonomous approval, or automatic publication.
- Human review is mandatory because deterministic cuts can still omit important
  moments, choose poor angles, expose private details, or produce audio
  discontinuities.
- The ±100 ms clap target must be verified manually at the clap point. Generated
  evidence records configured offsets but cannot prove perceptual synchronisation.
- Use only original or properly licensed music, fonts, and visual assets. This
  prototype adds no background music.

See `LICENSES.md` for software and asset licence notes.
