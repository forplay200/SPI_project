# AI-Assisted Multi-Camera Kindergarten Graduation Video Editing Pipeline

This repository implements a local, semi-automated, deterministic video-editing
prototype. Its Automatic Preparation Layer can discover likely camera sources,
suggest audio synchronization cues, and generate a rule-based JSON Editing
Decision List (EDL). Every generated camera choice remains explainable and
reviewable. The established manual EDL workflow is still available.

Despite the official project title, the implemented camera switching is rule-based.
It does not use machine learning and must not be described as doing so.

## Guided workflow user interface

The approved interface in `DESIGN.md` is implemented as a six-step local wizard:

1. Footage
2. Analysis
3. Synchronisation
4. Editing Plan
5. Draft Review
6. Approval

It adds a React/TypeScript frontend and a local FastAPI adapter in front of the
existing Python modules. The API calls discovery, grouping, sync, EDL, rendering,
evidence, review, and approval functions directly; it does not execute CLI commands
as subprocesses and does not duplicate the editing pipeline.

From the repository root on Windows PowerShell, start the API:

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In a second PowerShell window, install and start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. Interactive API documentation is available at
`http://127.0.0.1:8000/docs`; health is available at
`http://127.0.0.1:8000/api/health`.

The Footage screen accepts a workspace-relative local folder such as `input`.
The browser folder control is only a visual selection aid because browsers do not
expose arbitrary absolute paths; it never uploads footage. The backend independently
resolves and restricts input paths to this repository.

The UI shows all discovered and excluded files, selected/master cameras, complete
pair scores, sync candidates, offsets, confidence, verification state, generated
segments, transitions, overlays, and decision reasons. Camera selection can be
corrected explicitly after automatic grouping. EDL edits are limited to the
approved fields and pass through the existing validator before rendering.

The synchronisation page provides a local media preview starting near each cue.
Its compact waveform is currently a documented visual placeholder; the local
audio/video controls are the verification source. An automatically detected
shared transient is never labelled a verified clap. Grouping confidence and
manual clap acceptance remain separate.

Review checklist progress persists in the local browser. Smoke mode, unverified
sync, invalid duration, incomplete review, and checksum changes are visible
approval blockers. Approval remains a deliberate final action and promotes only
the exact reviewed SHA-256 without modifying or rerendering the video.

## Requirements

- Python 3.10 or newer
- Node.js 20 or newer and npm (guided UI)
- FastAPI and Uvicorn (local API)
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

The command discovers and probes local videos, scores every eligible pair using
local metadata and low-cost audio evidence, selects the best supported
multi-camera group, analyses the first 15 seconds for transient cues and up to
120 seconds for offset stability, generates configuration and an EDL, validates
them through the existing pipeline, and renders a draft only when safe. Filenames are supporting evidence only:
different prefixes, separators, Unicode names, and device time-zone differences
do not prevent audio comparison. The command never reviews, approves, publishes,
or uploads a video.

The equivalent one-line command is:

```powershell
python -m src.main auto --input input --duration 90 --title "Kindergarten Graduation Ceremony"
```

Customize the closing credit while the draft is being prepared:

```powershell
python -m src.main auto `
  --input input `
  --duration 20 `
  --title "Kindergarten Graduation Demo" `
  --credits "Edited by the Project Team | BTIS3053" `
  --credits-duration 4 `
  --allow-smoke
```

`--credits` defaults to the professional text `Edited by the Project Team`.
When `--credits-duration` is omitted, normal output uses four seconds and smoke
output preserves its compact one-second presentation default. Credit text must be
non-empty and an explicit duration must be finite and greater than zero. Both
values are written to `config/generated_project.json` and rendered by the
existing closing-credit screen.

Human-review warnings are deliberately not visible credit text. They remain in
console output, evidence, smoke/unverified filenames, review metadata, and approval
rules. Approval never edits or rerenders a reviewed video: it promotes only the
exact bytes whose SHA-256 is bound to the approved review record.

Generated files are written to:

- `config/generated_project.json`
- `config/generated_sync.json`
- `edl/generated_editing_decisions.json`
- `evidence/reports/video_discovery.json`
- `evidence/reports/camera_grouping.json`
- `evidence/reports/sync_candidates.json`
- `evidence/reports/generated_edl.json`
- `evidence/reports/automatic_preparation.json`
- `output/draft/` only when rendering is permitted

Files carrying the automation layer's provenance may be refreshed by a later
automatic run. Other content at a generated path requires `--overwrite`.
User-authored `config/project.json`, `config/sync.json`, and
`edl/editing_decisions.json` remain untouched.

### How automatic camera grouping works

Each source pair receives a transparent deterministic score recorded in
`camera_grouping.json`. Signals include normalized filename time, FFprobe creation
time, duration and common coverage, audio availability, envelope
cross-correlation, estimated offset, shared transient agreement, offset stability
across multiple windows, source confidence, and a derived-duplicate penalty. Audio
is decoded once per file to 8 kHz mono and cached for all pair comparisons; video
frames are not decoded for grouping.

Similar duration, codec, resolution, or filename alone cannot accept a pair.
Obvious `draft`, `final`, `rendered`, and `output` names are excluded by
default, and near-identical zero-offset stream copies receive a derived-copy
penalty. The report lists every accepted and rejected pair, its individual
signals, score, estimated offset, confidence, and reason.

Grouping reports `CAMERA_GROUP_CONFIRMED`, `CAMERA_GROUP_SUGGESTED`,
`CAMERA_GROUP_LOW_CONFIDENCE`, `NO_RELIABLE_CAMERA_GROUP`, or
`DERIVED_OUTPUTS_ONLY`. High-confidence groups may continue automatically;
medium-confidence groups may continue as an explicitly labelled smoke run. A
physically usable low-confidence best pair remains visible as a suggestion and
may continue only after `--continue-low-confidence`; an impossible or zero-overlap
pair remains blocked. Grouping confidence means the recordings probably cover
the same event. It does **not** verify that any transient is a deliberate clap or
satisfy the manual ±100 ms synchronization check.

Offset analysis rejects misleading correlation peaks that preserve less than 60%
of the shorter recording. It ranks overlap-preserving alternatives, compares
early, middle, and late windows, and records correlation, overlap, per-window
offsets, and stability. Suggested offsets of 10 seconds or more require stronger
correlation and stable multi-window evidence. These are conservative signal
checks, not semantic recognition of a clap, applause, or music.

## Assisted preparation workflow

Prepare and validate suggestions without rendering:

```powershell
python -m src.main prepare `
  --input input `
  --duration 90 `
  --title "Kindergarten Graduation Ceremony"
```

The same `--credits` and `--credits-duration` options are available to
`prepare`; they are validated and saved without rendering.

The summary reports one of the explicit states `READY_FOR_DRAFT`,
`READY_FOR_SMOKE_ONLY`, `NEEDS_CAMERA_SELECTION`,
`NEEDS_SYNC_CONFIRMATION`, `INSUFFICIENT_RENDERABLE_DURATION`, or `INVALID_INPUT`.
An automatically detected transient is never called a verified clap. Candidate
timestamps, prominence/correlation metrics, confidence, warnings, and
`requires_human_verification` are saved for review.

Duration reporting intentionally separates three concepts:

- **Common synchronized overlap** is the interval covered by every selected
  camera. It supports synchronization review only and is not an edit limit.
- **Total event coverage** is the union of synchronized camera timelines.
- **Maximum renderable duration** is the longest output supported by a valid
  deterministic EDL whose assigned camera covers every individual shot, while
  preserving shot, switch, transition, and source-boundary rules.

Accordingly, a valid edit can exceed common overlap when cameras started or
stopped at different times. Disconnected gaps are never filled, and footage is
not looped, frozen, slowed, or padded. The accepted decision is documented in
[`docs/adr/0001-coverage-based-renderability.md`](docs/adr/0001-coverage-based-renderability.md).

The individual preparation commands are:

```powershell
python -m src.main inspect --input input
python -m src.main detect-sync --input input
python -m src.main generate-edl `
  --config config/generated_project.json `
  --sync config/generated_sync.json `
  --duration 90
```

If automatic grouping is inconclusive, explicitly select two to four discovered
sources. This bypasses only group selection; probing, synchronization analysis,
duration and EDL validation, smoke labels, privacy controls, and approval
restrictions still apply:

```powershell
python -m src.main auto `
  --input input `
  --camera-file "video_20260619_151529.mp4" `
  --camera-file "VID_20260619_151529.mp4" `
  --duration 18 `
  --title "Kindergarten Graduation Demo" `
  --allow-smoke
```

A low-confidence but physically usable suggested group can instead be inspected
through the complete preparation path with an explicit human-verification flag:

```powershell
python -m src.main prepare `
  --input input `
  --duration 90 `
  --continue-low-confidence
```

If a human identifies the deliberate clap, record each verified source timestamp
without hand-editing JSON:

```powershell
python -m src.main confirm-sync `
  --sync config/generated_sync.json `
  --config config/generated_project.json `
  --camera camera_01 `
  --timestamp 5.695
```

All selected cameras must be confirmed before the generated sync file changes to
the `manual_clap` / `verified` state. Confirmation recomputes the exact common
timeline from `source_time = master_time + offset`, where each offset is the
camera cue timestamp minus the master cue timestamp. A large offset or a choice
that destroys most of the common timeline is rejected unless the operator has
visually or audibly checked the same cue and adds `--acknowledge-sync-risk`.

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

The current approved, read-only set contains four nested source recordings:

- `input/素材/Camera1/Camera1-1.mp4` — 125.109 seconds
- `input/素材/Camera2/Camera2-1.mp4` — 43.050 seconds
- `input/素材/Camera3/Camera3-1.mp4` — 95.713 seconds
- `input/素材/Camera4/Camera4-1.mp4` — 97.106 seconds

All four are factual angles of the same performance, but no deliberate clap has
yet been manually verified. Full-recording signal analysis currently suggests
Camera2/Camera4 most strongly: a shared audio alignment near +39.640 seconds has
0.826 correlation, full overlap of the shorter recording, and the same estimate
in all three analysis windows. It remains an unverified shared transient, not a
verified clap.

An earlier manual configuration used offsets `-2.800`, `+35.810`, and `+45.810`
seconds. The exact common-timeline calculation reduced usable EDL footage to
4.440 seconds and total output to 12.440 seconds; this was caused by unsafe manual
cue choices, not by the overlap formula. The confirmation workflow now reports
that loss and requires explicit risk acknowledgement for such values.

A requested 120-second output is still honestly impossible with the current
media: even the two longest sources cannot provide more than approximately
105.106 seconds including the normal title and credits. A real 20-second
`unverified-sync-smoke` draft has been rendered successfully from the strongest
automatic suggestion, but it is not submission-ready and cannot be approved.
Reproduce the non-acceptance render with:

```powershell
python -m src.main auto `
  --input input `
  --duration 20 `
  --title "Kindergarten Graduation Synchronisation Demo" `
  --allow-smoke `
  --overwrite
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

Run the frontend tests and production build:

```powershell
cd frontend
npm test
npm run lint
npm run format:check
npm run build
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
