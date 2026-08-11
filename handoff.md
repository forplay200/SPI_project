# Project Handoff

## 1. Project

- Name: AI-Assisted Multi-Camera Kindergarten Graduation Video Editing Pipeline
- Current branch: `interface`
- Repository path: `C:\Newfolder\SPI_project\SPI_project`
- Primary documents: `PRD_AI_Assisted_Multi_Camera_Kindergarten_v2.md`, `architecture.md`, `DESIGN.md`
- Last updated: 2026-07-29

## 2. Current Status

- Current milestone: Coverage-Based Renderability complete and verified
- Overall status: Automatic generation now distinguishes sync overlap, event-coverage union, and coverage-aware renderability; Python/API/frontend checks pass and the real 120-second request fails only on its true 65.466-second renderable limit
- Last completed task: Propagated the three duration metrics through generator, auto pipeline, evidence, FastAPI, guided UI, tests, ADR, and documentation
- Task currently in progress: None
- Next recommended task: Human-verify a deliberate synchronization cue and select a camera group with sufficient coverage before attempting an approval-eligible real draft

## 3. Completed Work

- [x] Created privacy-aware repository structure and ignore rules (`.gitignore`, `input/`, `output/`, `temp/`, `evidence/`)
- [x] Added immutable typed domain models and custom exceptions (`src/models.py`, `src/errors.py`)
- [x] Added logging and executable/dependency preflight (`src/logging_config.py`, `src/preflight.py`)
- [x] Added project, sync, EDL, and review-checklist examples (`config/`, `edl/`)
- [x] Implemented aggregated project/input validation (`src/validate_inputs.py`)
- [x] Implemented safe FFprobe JSON metadata extraction (`src/media_probe.py`)
- [x] Implemented manual clap offset parsing/calculation (`src/sync.py`)
- [x] Implemented JSON EDL parsing and semantic validation (`src/edl.py`)
- [x] Implemented renderer-neutral master-to-source mapping and summaries (`src/render_plan.py`)
- [x] Implemented renderer protocol and visible fallback selection (`src/renderer.py`)
- [x] Implemented MoviePy title, footage, overlay, transition, credit, audio, and cleanup behaviour (`src/moviepy_renderer.py`)
- [x] Implemented equivalent FFmpeg filter-graph rendering and command records (`src/ffmpeg_renderer.py`)
- [x] Implemented output stream/duration validation, SHA-256, and JSON evidence (`src/media_probe.py`, `src/evidence.py`)
- [x] Implemented temporary rendering and atomic draft promotion (`src/pipeline.py`)
- [x] Implemented complete review checklist, decision record, checksum validation, and final promotion (`src/review.py`)
- [x] Added thin CLI for preflight, validation, rendering, review, and approval (`src/main.py`)
- [x] Added 24 unit tests and 3 opt-in real-media integration tests (`tests/`)
- [x] Completed setup, format, workflow, privacy, capability, and limitation documentation (`README.md`)
- [x] Added software and asset licence record (`LICENSES.md`)
- [x] Probed all ten approved local media files without modifying originals (`evidence/reports/approved_input_inventory.json`)
- [x] Mapped stable `camera_wide` and `camera_close` IDs to approved read-only footage (`config/project.json`)
- [x] Analysed shared audio timing and sampled relevant frames locally (`temp/inspection/`)
- [x] Recorded the 5.695-second shared audio landmark as provisional and explicitly not a verified clap (`config/sync.json`)
- [x] Added and validated an honest 18-second approved-footage smoke plan (`config/smoke_project.json`, `edl/smoke_editing_decisions.json`)
- [x] Rendered and independently probed the corrected MoviePy smoke draft (`output/draft/kindergarten-graduation-demo-smoke_draft.mp4`)
- [ ] Rendered a compliant 60–180 second approved-footage draft (blocked: no source exceeds 25.57 seconds)

### Automatic Preparation Layer (2026-07-26)

- [x] Added recursive local discovery for MP4/MOV/MKV, output/temp/evidence exclusion, derived-name filtering, safe FFprobe metadata, display rotation, and stable deterministic camera IDs (`src/video_discovery.py`, `src/media_probe.py`)
- [x] Initially added conservative filename event-time grouping, then superseded it with the evidence-based grouping stage below; the helper remains only for compatibility (`src/video_discovery.py`)
- [x] Added non-destructive generated JSON handling; different generated config/EDL content requires `--overwrite` (`src/json_utils.py`)
- [x] Added deterministic local audio decoding, short-time energy/transient ranking, cross-camera envelope correlation, confidence states, no-timestamp low-confidence behavior, and human confirmation (`src/sync_assistant.py`)
- [x] Added typed automation outcome, discovery, sync candidate, and preparation result contracts (`src/models.py`)
- [x] Added deterministic common-timeline EDL generation with shot policy, camera rotation, three-switch minimum, transition, lower-third, explanations, source-boundary checks, provenance report, and existing-validator reuse (`src/edl_generator.py`)
- [x] Added `inspect`, `detect-sync`, `confirm-sync`, `generate-edl`, `prepare`, and `auto` while preserving all manual commands (`src/main.py`)
- [x] Added preparation/auto orchestration with explicit outcome summaries, unverified-sync filenames/evidence, smoke policy, serialized-artifact validation, and no approval call (`src/auto_pipeline.py`)
- [x] Prevented smoke and unverified-sync technical drafts from final approval (`src/review.py`)
- [x] Added unit coverage for discovery, filtering, stable IDs, generated config, sync candidates/offsets/confidence/no-audio/manual confirmation, deterministic EDLs, duration boundaries, orchestration, smoke labels, and non-approval (`tests/unit/`)
- [x] Added and executed a temporary synthetic 90-second two-camera automatic integration with a deterministic 300 ms audio cue offset and real FFmpeg fallback (`tests/integration/test_pipeline.py`)
- [x] Executed the approved-footage 18-second one-command auto smoke render; result is explicitly non-compliant and unverified-sync

### Evidence-based Camera Grouping (2026-07-26)

- [x] Reproduced the previous `NEEDS_CAMERA_SELECTION` result before changes: 10 discovered, 0 selected, filename evidence rejected all groups.
- [x] Added normalized compact, separated, prefixed, and Unicode filename timestamps plus FFprobe media creation time (`src/camera_grouping.py`, `src/media_probe.py`).
- [x] Added cached local 8 kHz mono analysis, all-pair envelope correlation, bounded offsets, shared transients, multi-window stability, transparent weighted scores, and rejection reasons (`src/camera_grouping.py`).
- [x] Added deterministic strongest-pair selection, controlled three/four-camera expansion, derived-copy penalties, confidence states, and `evidence/reports/camera_grouping.json`.
- [x] Added repeated `--camera-file` fallback to `detect-sync`, `prepare`, and `auto`; it bypasses grouping only.
- [x] Added local bundled FFmpeg/FFprobe discovery under ignored `temp/**/bin`, allowing the exact documented command to run without path flags in this workspace (`src/preflight.py`).
- [x] Added grouping/orchestration tests for filename formats, Unicode/no timestamp, positive/negative offsets, unrelated/low-confidence/no-audio pairs, duplicates, stable tie-breaking, best pair, three-camera selection, no reliable group, smoke grouping, and explicit selection.
- [x] Expanded the synthetic integration to A/B same-event sources with a known 300 ms offset, unrelated camera C, and an excluded derived output; project, sync, EDL, 90-second render, evidence, and non-approval all passed.
- [x] Ran the exact real command without explicit executable paths; 10 videos discovered, 3 derived excluded, 7 eligible, 21 pairs analyzed, three-camera group selected, and an 18-second unverified-sync smoke draft rendered.

### Configurable Generated Closing Credits (2026-07-27)

- [x] Added `--credits` and `--credits-duration` to both `prepare` and `auto`.
- [x] Replaced visible `Edited locally - human review required` with the professional default `Edited by the Project Team`.
- [x] Stored custom/default credit text and duration in `config/generated_project.json` and propagated them unchanged through the validated render plan.
- [x] Preserved the mandatory closing-credit screen in both MoviePy and FFmpeg.
- [x] Added early validation for blank credit text and non-positive/non-finite durations.
- [x] Kept human-review status in console/evidence/filenames/review policy rather than visible credit text.
- [x] Left checksum-bound approval unchanged; promotion still copies and verifies the exact reviewed bytes without rerendering.
- [x] Added focused unit coverage for CLI parsing, defaults, custom values, generated configuration, and duration validation; targeted run passed 19 tests.

### Guided Automation Workflow UI (2026-07-29)

- [x] Read the approved `DESIGN.md` and preserved the existing Python pipeline and CLI without redesign.
- [x] Added a local FastAPI application with health, preflight, OpenAPI, project CRUD, job status/cancellation, and all approved workflow route families (`backend/app/`).
- [x] Added persistent local UI project records, workspace-only input path validation, registered-file serving, and structured job states matching `DESIGN.md`.
- [x] Added direct service adapters for discovery/grouping, sync detection/confirmation/rejection, EDL generation/edit validation, rendering, evidence, review, and checksum-bound approval; no API route shells out to `src.main`.
- [x] Added initial API tests for health/OpenAPI, project persistence, path rejection, and truthful empty-input analysis (`backend/tests/test_api_foundation.py`).
- [x] Added the React/TypeScript/Vite/Tailwind/shadcn-style application shell with the exact approved colour tokens, typography, responsive layout, and six-step workflow stepper (`frontend/src/`).
- [x] Implemented project setup, camera analysis, manual group fallback, synchronisation verification, editable EDL timeline, draft playback/review, approval blockers, and evidence browser pages.
- [x] Added TanStack Query polling for every long-running job and preserved the exact approved job states.
- [x] Added local cue media preview; the compact waveform is honestly labelled as a placeholder and future work.
- [x] Added nine frontend tests across eight files, production TypeScript/Vite build verification, ESLint, and Prettier checks.
- [x] Executed the real approved-footage API workflow through analysis, sync, EDL, render, output validation, evidence, and approval prevention twice; the final run passed in 92.62 seconds.

### Automatic Synchronisation Regression Hardening (2026-07-29)

- [x] Reproduced `INSUFFICIENT_COMMON_DURATION` at 12.440 seconds from the four-camera UI sync file and traced it to manually entered cue timestamps, not the master/source interval formula.
- [x] Recorded the exact calculation: offsets `0`, `-2.800`, `+35.810`, and `+45.810` produced common master interval 2.800–7.240 seconds, 4.440 seconds of footage, and 12.440 seconds including normal title/credits.
- [x] Added overlap-preserving full-recording alignment with ranked alternatives, 60% minimum overlap, early/middle/late offset estimates, stability, and stronger large-offset evidence requirements (`src/sync_assistant.py`).
- [x] Added exact sync sanity evidence: formula, source bounds, offsets, common start/end/duration, zero-offset duration, preservation ratio, warnings, and errors (`src/sync_assistant.py`).
- [x] Prevented non-finite, negative, and out-of-source manual cue timestamps and required explicit `--acknowledge-sync-risk` for large or overlap-destroying confirmations.
- [x] Changed camera grouping to reuse cached full-window alignment evidence and retain physically usable low-confidence pairs as ranked suggestions rather than hard rejection (`src/camera_grouping.py`).
- [x] Added `--continue-low-confidence` and configurable `--alignment-window` to the relevant CLI preparation commands (`src/main.py`, `src/auto_pipeline.py`).
- [x] Added FastAPI and React support for **Continue with Human Verification**, alignment alternatives, sync sanity, and large-offset risk acknowledgement (`backend/`, `frontend/`).
- [x] Added regression tests for tiny-overlap false maxima, stable large positive/negative offsets, exact four-camera overlap math, risky manual confirmation, retained group suggestions, and automatic smoke continuation (`tests/unit/`, `frontend/src/test/`).
- [x] Analysed all six real approved-footage pairs and saved the complete diagnostics (`config/all_camera_sync_diagnostics.json`, `evidence/reports/all_camera_sync_diagnostics.json`).
- [x] Ran the real 120-second workflow: Camera2/Camera4 was selected at score 0.722232 with a stable +39.640-second shared-audio suggestion; the command truthfully stopped at maximum normal output 51.050 seconds.
- [x] Ran the real 20-second smoke workflow: MoviePy produced and validated `kindergarten-graduation-synchronisation-demo-unverified-sync-smoke_draft.mp4`; it remains unverified, smoke-labelled, approval-ineligible, and was not promoted.

### Coverage-Aware Duration Investigation (2026-07-29)

- [x] Confirmed `src/edl_generator.py` defines the generator maximum from `common_usable_timeline(config.cameras)`, the intersection of every selected camera's valid master interval.
- [x] Confirmed `src/render_plan.py` does not require all-camera overlap: it maps and validates only the camera assigned to each EDL segment.
- [x] Confirmed `src/edl.py` validates contiguous EDL duration, camera use, switches, transitions, and overlays but does not require every camera to cover every interval.
- [x] Confirmed `src/media_probe.py::validate_output` checks the rendered file against the render-plan duration and configured duration policy, not against all-camera overlap.
- [x] Executed an in-memory 120-second diagnostic EDL under the recorded four-camera offsets. Seven 16-second segments alternated Camera1/Camera4; semantic EDL validation and render-plan construction passed with six switches and valid source bounds.
- [x] Recorded the distinction: all-camera intersection is 4.440 seconds; configured non-negative master-timeline coverage union is 125.109 seconds; the tested renderable main duration is 112 seconds plus eight seconds of title/credits.
- [x] Determined the original 12.440-second rejection is caused by the generator equating common synchronized overlap with maximum renderable duration.
- [x] Determined the later Camera2/Camera4-only 120-second request still cannot reach 120 seconds, but its reported 51.050-second cap is conservative: current non-negative master coverage is 57.466 seconds (65.466 with normal presentation), while rebasing to Camera4 can expose 97.106 seconds (105.106 with presentation).
- [x] Implemented coverage-aware EDL generation and three-metric duration reporting; the earlier diagnostic is retained above as defect history.

### Coverage-Based Renderability Implementation (2026-07-29)

- [x] Added typed `CoverageInterval` and `DurationMetrics` contracts and replaced the obsolete outcome with `INSUFFICIENT_RENDERABLE_DURATION` (`src/models.py`).
- [x] Added synchronized coverage intervals, merged event union, all-camera overlap diagnostics, deterministic coverage-window scheduling, camera-sequence search, and maximum-renderability calculation (`src/edl_generator.py`).
- [x] Preserved the existing two-camera, three-switch, minimum/preferred/maximum shot, transition, lower-third, reason, semantic EDL, and render-plan source-boundary rules.
- [x] Added the exact four-camera 120-second regression: common overlap 4.440 seconds, event union 170.919 seconds, and a valid 112-second main EDL plus eight seconds of presentation.
- [x] Propagated all three metrics through automatic summaries, CLI output, preflight/render evidence, FastAPI analysis/sync/EDL/draft responses, frontend types, and guided workflow pages.
- [x] Added the accepted ADR `docs/adr/0001-coverage-based-renderability.md` and updated `README.md`, `architecture.md`, and `DESIGN.md`.
- [x] Re-ran the approved-footage 120-second command: Camera2/Camera4 remained unverified; common overlap 43.050 seconds, event coverage 97.106 seconds, maximum renderable output 65.466 seconds; result truthfully remained blocked with no EDL/draft/approval.

## 4. Files Created or Modified

- `.gitignore` — excludes all root/input video formats, generated drafts/finals, temporary media, logs, and caches; preserves directory keep files.
- `requirements.txt` — MoviePy, pytest, and Ruff version ranges.
- `pyproject.toml` — pytest discovery and Ruff configuration.
- `README.md` — installation, configuration, CLI, evidence, review, privacy, ethics, testing, and limitations.
- `LICENSES.md` — Python/MoviePy/FFmpeg/dependency/font/asset licence notes.
- `config/project.json` — two-camera project and configurable duration-policy example.
- `config/sync.json` — selected master camera, measured provisional cue, unconfirmed-clap status, and ±100 ms threshold.
- `config/smoke_project.json` — 640×360/15 fps approved-footage smoke configuration with a non-acceptance duration policy.
- `config/review_checklist.example.json` — all mandatory human review items.
- `edl/editing_decisions.json` — four contiguous segments, two cameras, three switches, transition, reason, and lower-third.
- `edl/smoke_editing_decisions.json` — four 4-second approved-footage segments for three real camera switches.
- `evidence/reports/approved_input_inventory.json` — complete FFprobe inventory, selected pair, sync assessment, review regions, and duration feasibility.
- `output/draft/kindergarten-graduation-demo-smoke_draft.mp4` — corrected local smoke artefact; 18.000 seconds, H.264/AAC, SHA-256 `5f723446dd155c46aa4abd72784af2f9cd4e7e1a29f0cb19639d6dcd9a05d683`.
- `src/models.py` — all configuration, media, EDL, plan, result, and review dataclasses.
- `src/errors.py` — explicit error taxonomy required by the architecture.
- `src/json_utils.py` — safe JSON reads and atomic JSON writes.
- `src/logging_config.py` — console/local file logging.
- `src/preflight.py` — MoviePy/FFmpeg/FFprobe availability and executable verification.
- `src/validate_inputs.py` — structural, path, extension, camera-count, uniqueness, master-camera, and output-policy checks.
- `src/media_probe.py` — FFprobe subprocess/JSON parser, creation-time extraction, and rendered-output validation.
- `src/sync.py` — sync config parser, offset formula, and immutable camera updates.
- `src/edl.py` — strict parser plus chronology, continuity, cameras, switches, duration, transition, and overlay checks.
- `src/render_plan.py` — offset mapping, boundary checks, immutable render instructions, printable summary.
- `src/renderer.py` — renderer protocol and controlled MoviePy-to-FFmpeg fallback.
- `src/moviepy_renderer.py` — MoviePy 1/2-compatible operations, Pillow-generated local text, silence where needed, and resource cleanup.
- `src/ffmpeg_renderer.py` — argument-array invocation, deterministic filter graph, captured outputs, and command log.
- `src/evidence.py` — preflight/render JSON evidence and streaming SHA-256.
- `src/pipeline.py` — prepared pipeline, temporary output, validation, atomic draft move, and evidence orchestration.
- `src/review.py` — checklist templates, strict review records, anti-tamper checks, and approved final promotion.
- `src/main.py` — CLI-only orchestration, prepare/auto credit options, alignment-window and low-confidence continuation flags, risk-aware sync confirmation, and non-zero expected-failure exit status.
- `tests/unit/` — validation, sync, EDL, render plan, FFprobe, renderer adapter, FFmpeg command, examples, and review tests.
- `tests/integration/test_pipeline.py` — real MoviePy render, deliberate real FFmpeg fallback, custom generated-credit propagation/rendering, 72-second contract render, output probing, evidence, and exact-byte approval workflow.
- `handoff.md` — this implementation and verification record.
- `backend/app/main.py` — FastAPI application factory, local CORS policy, service wiring, health, and OpenAPI host.
- `backend/app/api/routes.py` — typed project, analysis, sync, EDL, render, job, review, approval, evidence, and registered-file endpoints.
- `backend/app/schemas/api.py` — Pydantic project/job/workflow contracts, including every approved job state.
- `backend/app/services/project_service.py` — thread-safe local JSON project persistence under ignored `evidence/ui/`.
- `backend/app/services/job_service.py` — in-process jobs with real stage progress, structured failures, and safe-boundary cancellation.
- `backend/app/services/automation_service.py` — direct adapters to existing pipeline modules; no CLI subprocess calls.
- `backend/app/security/path_policy.py` — repository-bound input paths and exact registered-file policy.
- `backend/tests/` — API foundation/OpenAPI/path tests and opt-in real approved-footage UI integration.
- `frontend/package.json`, `frontend/package-lock.json` — approved React/Vite/Tailwind/shadcn/Lucide/TanStack/Router stack and verified toolchain.
- `frontend/src/api/` — typed HTTP contracts and API client.
- `frontend/src/components/` — shell, stepper, job progress, timeline, cue preview, checklist, and reusable UI primitives.
- `frontend/src/pages/` — all six guided screens plus the Evidence screen.
- `frontend/src/test/` — focused wizard, setup, analysis, sync, EDL, review, approval, and evidence tests.
- `frontend/src/styles.css`, `frontend/tailwind.config.ts` — exact approved tokens, typography, focus, and reduced-motion behavior.

- `src/video_discovery.py` — deterministic recursive discovery, exclusions, probing, stable IDs, reports, and conservative related-camera grouping.
- `src/camera_grouping.py` — deterministic multi-signal pair scoring, cached full-window audio analysis, overlap-aware alternatives, retained low-confidence suggestions, derived-copy detection, confidence states, and best-group selection.
- `src/sync_assistant.py` — local FFmpeg audio decoding, transient ranking, overlap-aware correlation alternatives, multi-window stability, exact timeline sanity evidence, confidence policy, and risk-aware human confirmation.
- `src/edl_generator.py` — synchronized common-duration calculation and validated deterministic EDL proposals.
- `src/auto_pipeline.py` — generated project configuration, configurable closing credits/alignment window, explicit low-confidence continuation, preparation outcomes, sanity warnings, summary evidence, and safe auto-draft orchestration.
- `tests/unit/test_video_discovery.py`, `test_sync_assistant.py`, `test_edl_generator.py`, `test_auto_pipeline.py` — focused automation tests, including generated credit defaults/customization/validation.
- `tests/unit/test_camera_grouping.py`, `test_preflight.py`, `test_media_probe.py` — grouping signals/selection, local executable resolution, and creation-time metadata coverage.
- `tests/integration/test_pipeline.py` — opt-in synthetic compliant automatic workflow with generated temporary media.
- `README.md`, `architecture.md` — automatic, assisted, expert, credit configuration, checksum-integrity, confidence, smoke, outcome-state, and privacy documentation.
- `config/generated_project.json`, `config/generated_sync.json`, `edl/generated_editing_decisions.json` — latest two-camera, 20-second real-footage smoke artifacts using Camera2/Camera4 and an unverified +39.640-second shared-audio alignment.
- `config/all_camera_sync_diagnostics.json` — machine-readable six-pair real-footage alignment alternatives, multi-window metrics, and sanity evidence.
- `evidence/reports/camera_grouping.json` — ignored local all-pair grouping evidence; six current real pairs with scores, offsets, confidence, and reasons.
- `evidence/reports/kindergarten-graduation-synchronisation-demo-unverified-sync-smoke_render.json` — MoviePy render evidence, output metadata, offsets, warnings, runtime, and SHA-256.
- `output/draft/kindergarten-graduation-synchronisation-demo-unverified-sync-smoke_draft.mp4` — ignored local 20-second automatic draft; never promoted or approved.

### Coverage-duration files (2026-07-29)

- `src/models.py` - typed coverage intervals, duration metrics, and corrected insufficient-renderability state.
- `src/edl_generator.py` - synchronized camera intervals, merged event coverage, deterministic per-shot availability scheduler, and renderability calculation.
- `src/auto_pipeline.py`, `src/main.py` - corrected outcome policy and three-metric reports/console output.
- `src/evidence.py`, `src/pipeline.py` - three metrics in preflight and render evidence.
- `backend/app/schemas/api.py`, `backend/app/api/routes.py`, `backend/app/services/automation_service.py` - typed API exposure and persisted workflow metrics.
- `frontend/src/api/types.ts`, `frontend/src/components/DurationMetricsPanel.tsx`, `frontend/src/pages/` - shared UI contract and Analysis, Synchronisation, Editing Plan, Review, and Evidence displays.
- `tests/unit/test_edl_generator.py`, `tests/unit/test_auto_pipeline.py`, `tests/integration/test_pipeline.py`, `backend/tests/`, `frontend/src/test/` - regression, API, evidence, and UI coverage.
- `docs/adr/0001-coverage-based-renderability.md`, `README.md`, `architecture.md`, `DESIGN.md` - accepted decision and user/developer documentation.
- `requirements.txt` - added `httpx2>=2,<3`, required by the currently resolved Starlette test client.

### Approved footage inventory

All paths below are under
`C:\Newfolder\SPI_project\SPI_project\input\`. FFprobe 8.1.2 read them
successfully. Every file has at least one video stream and AAC stereo audio at
48 kHz unless noted.

| File | Bytes | Duration | Video metadata | Notes |
|---|---:|---:|---|---|
| `Demo.mp4` | 55,667,094 | 21.973333 s | H.264, 1920×1080 stored, 29.798096 fps, rotation -90° | Camera candidate |
| `final_v1.mp4` | 21,483,391 | 24.321000 s | H.264, 1920×1080, 30 fps | Apparently derived output |
| `final_v2.mp4` | 18,934,778 | 24.088000 s | H.264, 608×1080, 30 fps | Apparently derived output |
| `teacher_demo_final.mp4` | 21,496,399 | 24.333000 s | H.264, 1920×1080, 30 fps | Apparently derived output |
| `VID20260619151534.mp4` | 125,219,042 | 19.863067 s | H.264, 3840×2160, 29.199922 fps | Camera candidate |
| `VID_20260619_151231 1.mp4` | 16,483,731 | 7.517233 s | H.264, 1920×1080, 30.301682 fps | Short pre-event candidate |
| `VID_20260619_151529.mp4` | 27,218,242 | 22.984778 s | H.264, 1280×720 stored, 29.906995 fps, rotation -90° | Selected as `camera_close` |
| `VID_20260619_151532 1.mp4` | 36,460,988 | 18.859122 s | H.264, 1920×1080 stored, 29.958906 fps, rotation -90° | Camera candidate |
| `video_20260619_151529.mp4` | 27,633,910 | 23.622104 s | HEVC, 1920×1080, 30.047197 fps | Selected master `camera_wide` |
| `视频-20260619-071529-f92c617d.mov` | 315,562,996 | 25.570000 s | HEVC, 3840×2160, 119.945248 fps | Also has a second 4-channel audio stream and six data streams |

Selected absolute paths:

- `camera_wide`: `C:\Newfolder\SPI_project\SPI_project\input\video_20260619_151529.mp4`
- `camera_close`: `C:\Newfolder\SPI_project\SPI_project\input\VID_20260619_151529.mp4`

The originals were opened read-only for probing/decoding only. They were not
modified, moved, renamed, deleted, or staged.

The inventory above records the previously supplied ten-file set and remains as
historical evidence. It is superseded for the current session by these four
approved, read-only files:

| Current file | Bytes | Duration | Video/audio metadata |
|---|---:|---:|---|
| `素材/Camera1/Camera1-1.mp4` | 154,797,374 | 125.109002 s | H.264 1920x1080 at 30 fps; AAC stereo 48 kHz |
| `素材/Camera2/Camera2-1.mp4` | 55,359,502 | 43.050000 s | H.264 1920x1080 at 30 fps; AAC stereo 48 kHz |
| `素材/Camera3/Camera3-1.mp4` | 116,346,244 | 95.712993 s | H.264 1920x1080 at 30 fps; AAC stereo 48 kHz |
| `素材/Camera4/Camera4-1.mp4` | 119,315,947 | 97.106009 s | H.264 1920x1080 at 30 fps; AAC stereo 48 kHz |

All current files were discovered recursively, probed, and audio-decoded locally
without moving, renaming, deleting, overwriting, staging, or uploading them.

## 5. Architecture and Implementation Decisions

- Decision: The Automatic Preparation Layer is additive and feeds the existing strict pipeline.
  - Reason: Existing validation, render planning, atomic promotion, evidence, review, and checksum approval are working safety boundaries.
  - Consequences: Generated JSON is reloaded through `prepare_pipeline`; validators were not weakened.
  - Affected files: `src/auto_pipeline.py`, `src/edl_generator.py`, `src/main.py`.
- Decision: Closing-credit wording is fixed during preparation, never during approval.
  - Reason: Approval is bound to the exact reviewed SHA-256 and must not mutate or rerender media.
  - Consequences: `--credits` and `--credits-duration` populate generated project configuration and the existing render plan. The default visible text is `Edited by the Project Team`; review warnings remain operational metadata.
  - Affected files: `src/auto_pipeline.py`, `src/main.py`, `README.md`, `architecture.md`; `src/review.py` intentionally unchanged.
- Decision: An omitted credit duration preserves existing mode-specific presentation timing.
  - Reason: Normal output already used four seconds while short non-acceptance smoke output used one second.
  - Consequences: `--credits-duration` overrides either mode, but omission remains four seconds normally and one second for smoke.
  - Affected files: `src/auto_pipeline.py`, `tests/unit/test_auto_pipeline.py`.
- Decision: The earlier filename-only camera grouping rule is superseded by deterministic multi-signal pairwise grouping.
  - Reason: Filename formats and device clocks vary; local audio similarity, offset stability, shared transients, metadata time, and common coverage provide stronger explainable evidence.
  - Consequences: Every eligible pair is analyzed and reported. Audio evidence and minimum duration are mandatory; filename, codec, resolution, or duration similarity alone cannot accept a pair.
  - Affected files: `src/camera_grouping.py`, `src/video_discovery.py`, `src/media_probe.py`, `src/auto_pipeline.py`.
- Decision: The strongest accepted pair anchors group selection; larger groups require all-high-confidence edges within 0.05 of that pair.
  - Reason: Pure maximum-clique selection admitted a larger but weaker real-footage group whose initial sync window could not support every source.
  - Consequences: Three or four cameras are still selected when mutually coherent, while weak coincidental links cannot displace the best pair. Stable IDs break ties.
  - Affected files: `src/camera_grouping.py`, `tests/unit/test_camera_grouping.py`.
- Decision: Grouping confidence and synchronization acceptance remain separate.
  - Reason: Strong shared-event audio can support camera grouping without proving that a transient is a deliberate clap.
  - Consequences: The real draft is named `unverified-sync-smoke`, evidence requires human verification, and final approval remains prohibited.
  - Affected files: `src/camera_grouping.py`, `src/sync_assistant.py`, `src/auto_pipeline.py`, `src/review.py`.
- Decision: Cross-camera correlation may select an unverified shared transient, never a verified clap.
  - Reason: Signal evidence supports offset estimation but cannot establish a deliberate clap or manual acceptance.
  - Consequences: Auto evidence and filenames remain `unverified-sync`; human confirmation is required.
  - Affected files: `src/sync_assistant.py`, `src/auto_pipeline.py`, `src/evidence.py`.
- Decision: Smoke and unverified-sync drafts are ineligible for approval.
  - Reason: Technical rendering success must not be confused with a compliant, manually verified submission.
  - Consequences: Approved review records reject these clearly labelled filenames.
  - Affected files: `src/review.py`, `tests/unit/test_review.py`.

- Decision: Cross-correlation candidates must preserve at least 60% of the shorter source and are ranked by overlap-weighted evidence.
  - Reason: A raw correlation maximum for Camera1/Camera2 occurred near +42.800 seconds with only about 0.240 seconds of overlap; it was a boundary artefact, not a trustworthy event alignment.
  - Consequences: Tiny-overlap local maxima are excluded. Reports retain separated alternatives and early/middle/late estimates so an operator can audit the selected lag.
  - Affected files: `src/sync_assistant.py`, `src/camera_grouping.py`, `tests/unit/test_sync_assistant.py`.
- Decision: Suggested offsets of 10 seconds or more require correlation of at least 0.70, at least 0.80 stability, and support in multiple windows before automatic use.
  - Reason: Large shifts can destroy most of the common timeline and are easier to obtain accidentally from repetitive applause, speech, or music.
  - Consequences: Camera2/Camera4's +39.640-second suggestion is usable for a clearly labelled smoke draft because correlation is 0.825633 and all three windows agree, but it remains an unverified shared transient.
  - Affected files: `src/sync_assistant.py`, `src/auto_pipeline.py`, `architecture.md`, `README.md`.
- Decision: Manual verification remains authoritative but is no longer accepted blindly.
  - Reason: The UI previously allowed arbitrary nonnegative timestamps and marked all-camera input verified even when those values collapsed usable footage from 43.050 seconds at zero offset to 4.440 seconds.
  - Consequences: Source bounds and exact common overlap are recalculated at confirmation time; risky choices require a separately recorded acknowledgement. The offset formula and SHA-bound approval rules are unchanged.
  - Affected files: `src/sync_assistant.py`, `src/main.py`, `backend/app/services/automation_service.py`, `frontend/src/pages/SynchronisationPage.tsx`.
- Decision: Physically usable below-threshold camera pairs remain suggestions rather than disappearing as invalid selections.
  - Reason: Confidence is graded evidence, while hard invalidity is reserved for unreadable media, missing coverage, derived-only input, or no usable overlap.
  - Consequences: CLI and UI can continue only through explicit human verification; downstream probe, sync, duration, EDL, smoke, privacy, and approval controls still apply.
  - Affected files: `src/models.py`, `src/camera_grouping.py`, `src/auto_pipeline.py`, `backend/`, `frontend/`.

- Decision: The default duration policy is configurable 60–180 seconds and includes opening title and closing credits.
  - Reason: The explicit implementation instruction and PRD primary objective use 60–180 seconds, while other PRD/architecture passages use 60–80.
  - Consequences: The sample produces 64 seconds of EDL footage plus 8 seconds of presentation screens (72 seconds). Setting the maximum to 80 requires configuration only.
  - Affected files: `src/models.py`, `src/edl.py`, `src/media_probe.py`, `config/project.json`, `README.md`.
- Decision: Approved footage remains read-only, local, and ignored by Git.
  - Reason: The user authorised local academic inspection/rendering but prohibited uploads, commits, and original-file mutation.
  - Consequences: All ten files were probed; only the selected pair was decoded for local audio/frame inspection and smoke rendering. Originals were not modified, moved, renamed, deleted, or staged.
  - Affected files: `.gitignore`, `config/project.json`, `evidence/reports/approved_input_inventory.json`.
- Decision: The measured 5.695-second landmark is not represented as a verified clap.
  - Reason: Waveform/spectrogram analysis found a shared transient, but sampled frames at 0–3 s, 5.3–6.1 s, and 14.1–15.1 s did not show a deliberate clap.
  - Consequences: `cue_type` is `shared_audio_transient_unconfirmed_as_clap`, `clap_time_seconds` is `null` in evidence, and `acceptance_status` remains `manual_clap_review_required`. The zero offset is used only for smoke testing.
  - Affected files: `config/sync.json`, `src/models.py`, `src/sync.py`, `src/evidence.py`, `README.md`.
- Decision: Do not manufacture a 60-second result from the short approved sources.
  - Reason: The selected common timeline is 22.984778 seconds; a valid full render can reach only 30.984778 seconds with the configured four-second title and credits.
  - Consequences: No repetition, time stretching, fabricated offset, or excessive title/credit padding was introduced. The canonical full plan remains rejected at preflight, and an explicitly labelled smoke configuration is used instead.
  - Affected files: `config/project.json`, `config/smoke_project.json`, `edl/editing_decisions.json`, `edl/smoke_editing_decisions.json`.
- Decision: All timeline-domain modules remain renderer-neutral.
  - Reason: Preserves the architecture boundary and makes fallback deterministic/testable.
  - Consequences: MoviePy imports occur only inside `src/moviepy_renderer.py`; sync, EDL, and render-plan modules have no renderer imports.
  - Affected files: `src/sync.py`, `src/edl.py`, `src/render_plan.py`, renderers.
- Decision: Text is generated locally with Pillow for MoviePy and `drawtext` for FFmpeg.
  - Reason: Avoids cloud services and MoviePy/ImageMagick coupling while producing readable title, overlay, and credits.
  - Consequences: The selected local font/build must be included in the asset/software licence review.
  - Affected files: `src/moviepy_renderer.py`, `src/ffmpeg_renderer.py`, `LICENSES.md`.
- Decision: Renderers write only a unique `.partial.mp4` under `temp/`.
  - Reason: Failed or unvalidated bytes must never be presented as a draft.
  - Consequences: Only a successfully probed output is atomically moved to `output/draft/`; renderers never write final files.
  - Affected files: `src/pipeline.py`.
- Decision: Approval records and final destinations are validated again during promotion.
  - Reason: A hand-edited record or changed draft must not bypass human-review controls.
  - Consequences: Approved records require every checklist value, a valid SHA-256, the exact draft path, and `output/draft` to `output/final` promotion.
  - Affected files: `src/review.py`, `tests/unit/test_review.py`.
- Decision: Direct FFmpeg and FFprobe calls always use argument arrays and `shell=False`.
  - Reason: Prevents command injection and matches the architecture.
  - Consequences: Filter graphs are data arguments and are saved locally for reproduction.
  - Affected files: `src/media_probe.py`, `src/ffmpeg_renderer.py`.

- Decision: The UI is a thin local adapter around `src/`, not a new editing implementation.
  - Reason: The approved design and user instruction require the working validation, grouping, sync, EDL, rendering, evidence, review, and approval boundaries to remain authoritative.
  - Consequences: FastAPI calls the Python functions directly. CLI behavior remains unchanged and no route shells out to `python -m src.main`.
  - Affected files: `backend/app/services/automation_service.py`, `backend/app/api/routes.py`.
- Decision: UI-generated artefacts use project-specific filenames while manual JSON remains untouched.
  - Reason: Multiple saved UI projects need stable local records without overwriting expert-authored configuration.
  - Consequences: Project/sync/EDL files use ignored `project-<id>` names; evidence and selections persist under ignored `evidence/ui/` and can be restored after API restart.
  - Affected files: `.gitignore`, `backend/app/services/project_service.py`, `backend/app/services/automation_service.py`.
- Decision: Browser path and file serving use explicit local allowlists.
  - Reason: A web request must not become arbitrary filesystem access.
  - Consequences: Input directories must remain inside the repository and media/evidence routes serve only exact files registered to the current project.
  - Affected files: `backend/app/security/path_policy.py`, `backend/app/api/routes.py`.
- Decision: The sync waveform graphic is a labelled placeholder; the registered local media player is the verification mechanism.
  - Reason: A compact visual waveform can be added later without inventing decoded samples or weakening the manual clap rule.
  - Consequences: Cue preview seeks near the candidate, while the UI explicitly states that the waveform is not evidence.
  - Affected files: `frontend/src/components/WaveformPreview.tsx`, `README.md`, `architecture.md`.
- Decision: Approval eligibility is recomputed from current draft/config/sync/review/checksum state.
  - Reason: Cached UI state must never enable approval after a draft or policy changes.
  - Consequences: Smoke, unverified sync, invalid duration, missing/incomplete review, filename markers, and SHA-256 mismatch are explicit blockers; final promotion still uses `src.review.promote_approved_draft` unchanged.
  - Affected files: `backend/app/services/automation_service.py`, `frontend/src/pages/ApprovalPage.tsx`.

- Decision: Renderability is based on valid per-segment camera coverage, not all-camera intersection.
  - Reason: The existing renderer checks only the source camera assigned to each segment; cameras that start or stop at different event times can still form a continuous valid edit.
  - Consequences: `common_overlap_duration` is sync-only, `total_event_coverage` is the synchronized union, and `maximum_renderable_duration` is the generation constraint. Disconnected gaps are not filled, negative master time is not silently rebased, and source-boundary validation remains unchanged.
  - Affected files: `src/models.py`, `src/edl_generator.py`, `src/auto_pipeline.py`, `src/evidence.py`, `src/pipeline.py`, backend/frontend contracts and pages, tests, and `docs/adr/0001-coverage-based-renderability.md`.
- Decision: Maximum renderable output includes configured title and credit screens; overlap and event coverage remain footage-only metrics.
  - Reason: Requested project duration and existing duration policy include presentation screens, while overlap/union definitions describe synchronized source media.
  - Consequences: The approved Camera2/Camera4 result reports 43.050 seconds overlap, 97.106 seconds event coverage, and 65.466 seconds maximum renderable output under the current non-negative master timeline and switching constraints.
  - Affected files: `src/edl_generator.py`, UI labels, README, architecture, ADR.

## 6. Commands Executed

- Repository/document inspection:
  - `git status --short --branch`
  - `rg --files`
  - Full reads of the PRD and all 1,184 architecture lines
  - `git log -5 --oneline --decorate`
- Environment/dependencies:
  - Bundled Python version and package checks
  - `python -m pip install -r requirements.txt imageio-ffmpeg`
  - Downloaded/extracted FFmpeg 8.1.2 essentials under ignored `temp/` for local verification
  - `python -m pip install ruff`
- Approved-footage inspection and execution:
  - Recursive local media inventory under `input/`
  - FFprobe 8.1.2 JSON extraction for all ten approved files
  - SHA-256 reads for input identity checking; no originals changed
  - Local FFmpeg mono-audio decoding for waveform-envelope correlation
  - Local waveform/spectrogram generation and frame sampling under ignored `temp/inspection/`
  - `python -m src.main validate --ffprobe <local ffprobe>` (expected full-plan failure)
  - `python -m src.main validate --config config/smoke_project.json --sync config/sync.json --edl edl/smoke_editing_decisions.json --ffprobe <local ffprobe>`
  - `python -m src.main render --config config/smoke_project.json --sync config/sync.json --edl edl/smoke_editing_decisions.json --ffmpeg <local ffmpeg> --ffprobe <local ffprobe>` (run twice; first revealed an unsupported title glyph, second is the retained corrected draft)
  - Independent FFprobe stream/duration inspection and `Get-FileHash -Algorithm SHA256` on the retained smoke draft
- Validation/testing:
  - `python -m unittest discover -s tests -v`
  - `python -m pytest -q`
  - Opt-in integration runs with explicit `PIPELINE_TEST_FFMPEG` and `PIPELINE_TEST_FFPROBE`
  - `python -m pytest tests/integration/test_pipeline.py -q`
  - `python -m pytest tests/unit/test_examples.py -q`
  - `python -m compileall -q src tests`
  - `python -m ruff check src tests`
  - `python -m ruff format --check src tests`
  - `python -m src.main preflight --ffmpeg <local path> --ffprobe <local path>`
- Repository consistency:
  - `git diff --check`
  - source scans for placeholders, `shell=True`, prohibited capability claims, improper renderer imports, and final-output writes

### Automatic-layer commands

- `python -m src.main inspect --input input --ffprobe <local ffprobe>`
- `python -m src.main detect-sync --input input --ffmpeg <local ffmpeg> --ffprobe <local ffprobe> --overwrite`
- `python -m src.main prepare --input input --duration 90 --title "Kindergarten Graduation Ceremony" --ffmpeg <local ffmpeg> --ffprobe <local ffprobe> --overwrite`
- `python -m src.main prepare --input input --duration 18 --title "Kindergarten Graduation Ceremony" --allow-smoke --ffmpeg <local ffmpeg> --ffprobe <local ffprobe> --overwrite`
- `python -m src.main validate --config config/generated_project.json --sync config/generated_sync.json --edl edl/generated_editing_decisions.json --ffprobe <local ffprobe>`
- `python -m src.main auto --input input --duration 18 --title "Kindergarten Graduation Ceremony" --allow-smoke --ffmpeg <local ffmpeg> --ffprobe <local ffprobe>`
- Independent FFprobe JSON and PowerShell SHA-256 inspection of the generated auto smoke draft.
- Opt-in synthetic test: `pytest tests/integration/test_pipeline.py::PipelineIntegrationTests::test_automatic_synthetic_clap_workflow_renders_compliant_draft -q` with local FFmpeg/FFprobe environment variables.

### Evidence-based grouping commands

- Reproduced before implementation: `python -m src.main auto --input input --duration 18 --title "Kindergarten Graduation Demo" --allow-smoke` — 10 discovered, 0 usable selected, `NEEDS_CAMERA_SELECTION`, filename-only warning.
- Targeted grouping/orchestration: `python -m pytest tests/unit/test_camera_grouping.py tests/unit/test_auto_pipeline.py -q` — 12 passed.
- Synthetic relevant/unrelated/derived integration: opt-in `python -m pytest tests/integration/test_pipeline.py::PipelineIntegrationTests::test_automatic_synthetic_clap_workflow_renders_compliant_draft -q` — 1 passed in 7.77 s.
- Full media-enabled suite with explicit local FFmpeg/FFprobe environment variables: `python -m pytest -q` — 58 passed in 16.82 s.
- Required ordinary suite: `python -m pytest -q` — 54 passed, 4 skipped in 0.44 s; skips are the opt-in real-media tests.
- Required static checks: `python -m ruff check src tests`, `python -m ruff format --check src tests`, and `python -m compileall -q src tests` — all passed; 42 Python files formatted.
- Exact real workflow: `python -m src.main auto --input input --duration 18 --title "Kindergarten Graduation Demo" --allow-smoke` — passed without explicit executable paths in 92.8 s.
- Generated-artifact validation: `python -m src.main validate --config config/generated_project.json --sync config/generated_sync.json --edl edl/generated_editing_decisions.json` — passed; 18.000 s plan, three cameras, four segments, three switches.
- Independent real draft probe: local FFprobe `-show_entries format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate` — 18.000000 s, H.264 1280×720 at 30 fps, AAC audio.
- Independent `Get-FileHash -Algorithm SHA256` matched evidence (`7DB5CF4D202AE7360963E03E0537C78E57FD3548272BCCC00170C1F8C734F377`); `output/final` contained zero promoted outputs.

### Configurable-credit commands

- Focused regression: `python -m pytest tests/unit/test_auto_pipeline.py tests/unit/test_validation.py tests/unit/test_render_plan.py tests/unit/test_review.py -q` — 19 passed in 0.93 s.
- Real requested workflow: `python -m src.main auto --input input --duration 20 --title "Kindergarten Graduation Demo" --credits "Edited by the Project Team | BTIS3053" --credits-duration 4 --allow-smoke` — passed in 121.7 s.
- Independent output probe: local FFprobe reported 20.000000 s, H.264 1280×720 at 30 fps, and AAC audio.
- Generated-artifact validation: `python -m src.main validate --config config/generated_project.json --sync config/generated_sync.json --edl edl/generated_editing_decisions.json` — passed; 20.000 s, four segments, three switches, custom four-second closing credit.
- Closing-screen inspection: extracted the frame at 18.0 s to ignored `temp/inspection/custom_credits.png`; it visibly contains `Edited by the Project Team | BTIS3053` and no review-warning text.
- Media-enabled full suite with local FFmpeg/FFprobe: `python -m pytest -q` — 62 passed in 24.31 s.
- Final required ordinary suite: `python -m pytest -q` — 58 passed, 4 skipped in 0.56 s; the skips are opt-in media tests.
- Static verification: `python -m ruff check src tests`, `python -m ruff format --check src tests`, and `python -m compileall -q src tests` — all passed; 42 Python files formatted.

### Synchronisation-regression commands (2026-07-29)

- Exact pre-fix reproduction: `python -m src.main auto --input input --duration 120 --title "Kindergarten Graduation Synchronisation Regression" --overwrite` — four videos discovered, six pairs analysed, score 0.383, `CAMERA_GROUP_LOW_CONFIDENCE`, no selection, `NEEDS_CAMERA_SELECTION`.
- Existing UI artifact reproduction: `python -m src.main generate-edl --config config/project-efc9ec27e3b5_project.json --sync config/project-efc9ec27e3b5_sync.json --duration 120` — failed truthfully with maximum honest output 12.440 seconds.
- Full four-camera diagnostics: `python -m src.main detect-sync --input input --alignment-window 120 --continue-low-confidence --overwrite` plus local all-pair analysis — all six pairs decoded once per source and written to `config/all_camera_sync_diagnostics.json` and ignored evidence.
- Post-fix 120-second run: `python -m src.main auto --input input --duration 120 --title "Kindergarten Graduation Synchronisation Regression" --continue-low-confidence --overwrite` — four usable candidates, six pairs, Camera2/Camera4 selected, score 0.722232, `CAMERA_GROUP_SUGGESTED`, unverified +39.640-second alignment, `INSUFFICIENT_COMMON_DURATION`, maximum honest normal output 51.050 seconds, no draft.
- Real smoke render: `python -m src.main auto --input input --duration 20 --title "Kindergarten Graduation Synchronisation Demo" --allow-smoke --overwrite` — `DRAFT_RENDERED_WITH_UNVERIFIED_SYNC` in 109.9 seconds; MoviePy rendering itself took 107.032 seconds.
- Independent probe/hash: rendered output is 20.000 seconds, H.264/AAC, 1280x720, 30 fps; SHA-256 `ad16868b74f54a8e3af433ebcad99960db72e5955ec82f009b23c6b934b354f8`, matching render evidence.
- Targeted regression suite: `python -m pytest tests/unit/test_sync_assistant.py tests/unit/test_camera_grouping.py tests/unit/test_auto_pipeline.py -q` — 27 passed.
- Final ordinary Python suite: `python -m pytest -q` — 67 passed, 5 skipped, one Starlette deprecation warning and one sandbox cache warning; no failures.
- Final Python static checks: `python -m ruff check backend src tests`, `python -m ruff format --check backend src tests`, and `python -m compileall -q backend src tests` — all passed; 58 files already formatted.
- Final frontend checks: `vitest run --configLoader runner` — 10 passed across eight files; `npm run lint` and `npm run format:check` passed.
- Frontend production build: `vite build --configLoader runner --outDir ../temp/frontend-regression-build-final2` — passed, 1,735 modules, 390.56 kB JavaScript (123.39 kB gzip). A separate ignored output was used because Windows denied cleanup of the existing `frontend/dist` directory.
- Repository consistency: `git diff --check` passed; the exact generated pytest scratch directory was removed after its validated workspace path was confirmed.
- Coverage-duration investigation: read-only source trace through `src/edl_generator.py`, `src/render_plan.py`, `src/edl.py`, `src/pipeline.py`, and `src/media_probe.py`; no implementation change made.
- In-memory coverage proof: constructed a 112-second, seven-segment Camera1/Camera4 EDL using the recorded offsets, then called `validate_edl` and `build_render_plan`. Result: passed, six switches, expected final duration 120.000 seconds, and every mapped source interval remained within its assigned camera.
- Interrupted opt-in media-suite rerun was explicitly terminated after the user changed the active request; no result is claimed for that aborted run.

### Coverage-renderability commands (2026-07-29)

- `\.venv\Scripts\python.exe -m pytest tests\unit\test_edl_generator.py -q` - final targeted run 7 passed.
- `\.venv\Scripts\python.exe -m pytest tests\unit\test_auto_pipeline.py -q` - 9 passed.
- `\.venv\Scripts\python.exe -m pytest tests\unit -q` - 65 passed.
- `\.venv\Scripts\python.exe -m pytest backend\tests -q --basetemp .test-temp\backend-coverage` - 4 passed, 1 skipped.
- Final full run: `\.venv\Scripts\python.exe -m pytest -q --basetemp temp\pytest-coverage-final -p no:cacheprovider` - 70 passed, 5 skipped.
- `npm test` - 10 passed across 8 frontend files.
- `npm run lint`, `npm run format:check`, `npm run build` - passed; Vite transformed 1,736 modules.
- `\.venv\Scripts\python.exe -m ruff check src tests backend`, `ruff format --check`, and `compileall -q src tests backend` - passed; 58 Python files formatted.
- `\.venv\Scripts\python.exe -m pip install "httpx2>=2,<3"` - installed `httpx2 2.9.1`, `httpcore2 2.9.1`, and `truststore 0.10.4` for current Starlette TestClient compatibility.
- Real approved-footage check: `\.venv\Scripts\python.exe -m src.main auto --input input --duration 120 --title "Kindergarten Graduation Synchronisation Regression" --continue-low-confidence --overwrite` - expected exit 1; no EDL, draft, or approval because maximum renderable output is 65.466 seconds.

## 7. Test and Verification Results

- Initial validation/render-plan unit run (2026-07-26):
  - Command: `python -m unittest discover -s tests -v`
  - Passed: 14
  - Failed: 0
  - Skipped: 0
- Renderer/review unit run (2026-07-26):
  - Command: `python -m unittest discover -s tests -v`
  - Passed: 21
  - Failed: 0
  - Skipped: 0
- First real-media integration run (2026-07-26):
  - Command: opt-in `pytest tests/integration/test_pipeline.py -q`
  - Passed: 1
  - Failed: 1
  - Skipped: 0
  - Failure: FFmpeg lower-third `drawbox` used a self-referential width expression.
  - Resolution: Replaced it with validated numeric canvas coordinates and reran the failure.
- Targeted FFmpeg fallback rerun (2026-07-26):
  - Passed: 1
  - Failed: 0
  - Skipped: 0
- Real-media integration suite after fix (2026-07-26):
  - Passed: 3
  - Failed: 0
  - Skipped: 0
  - Verified: MoviePy draft, deliberate FFmpeg fallback, video/audio streams, atomic promotion, evidence, SHA-256, checksum-bound approval, final separation, and a 72-second output.
- Previous full synthetic-media suite (2026-07-26):
  - Command: opt-in full `python -m pytest -q`
  - Passed: 27
  - Failed: 0
  - Skipped: 0
  - Runtime: 9.64 seconds
- Current normal dependency-independent baseline (2026-07-26):
  - Command: `python -m pytest -q`
  - Passed: 25
  - Failed: 0
  - Skipped: 3 opt-in real-media integration tests
  - Runtime: 0.19 seconds
- Approved-footage inventory and sync assessment (2026-07-26):
  - FFprobe files passed: 10
  - FFprobe files failed: 0
  - Selected pair: `camera_wide` / `camera_close`
  - Measured shared landmark: 5.695 seconds in both files
  - Verified deliberate clap: no
  - Regions sampled for manual review: 0.0–3.0 s, 5.3–6.1 s, and 14.1–15.1 s in both selected files
- Canonical approved-footage validation (2026-07-26):
  - Exit code: 1
  - Failure: segment ends at 32, 48, and 64 seconds exceed source durations of 22.984778 and 23.622104 seconds.
  - Classification: source-duration blocker, not a code defect.
- Approved-footage smoke validation (2026-07-26):
  - Exit code: 0
  - Expected output: 18.000 seconds
  - Cameras: 2
  - Switches: 3
- First approved-footage smoke render (2026-07-26):
  - Renderer: MoviePy
  - Technical validation: passed at exactly 18.000 seconds with H.264/AAC.
  - Visual QA: failed one title glyph because the fallback local font did not support the em dash.
  - Resolution: changed the smoke title to use an ASCII hyphen and rerendered.
- Retained approved-footage smoke render (2026-07-26):
  - Path: `output/draft/kindergarten-graduation-demo-smoke_draft.mp4`
  - Renderer: MoviePy; fallback activated: no
  - Runtime: 12.672 seconds on the final evidence-generating rerender
  - Actual duration: 18.000 seconds
  - Video: H.264, 640×360, 15 fps
  - Audio: AAC stereo, 44.1 kHz
  - Size: 660,387 bytes
  - SHA-256: `5f723446dd155c46aa4abd72784af2f9cd4e7e1a29f0cb19639d6dcd9a05d683`
  - Visual samples: corrected title readable; lower-third visible; credits readable.
- Final regression suite after honest cue-evidence changes (2026-07-26):
  - Command: opt-in full `python -m pytest -q`
  - Passed: 28
  - Failed: 0
  - Skipped: 0
  - Runtime: 9.31 seconds
- Final static checks:
  - `python -m ruff check src tests`: passed
  - `python -m ruff format --check src tests`: 31 files formatted
  - `python -m compileall -q src tests`: passed
- Final preflight with explicit local tools:
  - MoviePy available: yes
  - FFmpeg available: yes
  - FFprobe available: yes
  - Selected renderer ready: yes
  - Warnings: none
- Shipped example consistency:
  - Passed: project config, sync config, EDL, 2.2-second camera offset, 3 switches, and 72-second plan.
- Tests not executed:
  - No compliant 60–180 second approved-footage render was executed because validation proves the source duration is insufficient.
- Manual checks still required:
  - A human must listen to the selected files around 0.0–3.0 s, 5.3–6.1 s, and 14.1–15.1 s to confirm whether any audible event can legitimately serve as a clap.
  - The smoke draft is a technical artefact, not an approved final. Any future full draft requires complete visual/audio/privacy/licensing review and checklist completion.

### Automatic Preparation Layer results (2026-07-26)

- Pre-automation baseline: `python -m pytest -q` — 25 passed, 3 skipped.
- Focused discovery tests — 3 passed.
- Focused sync/discovery tests — 8 passed.
- Focused EDL generator tests — 4 passed.
- Focused orchestration/review tests — 8 passed.
- Final ordinary suite — 43 passed, 4 skipped in 0.39 s.
- Final opt-in full suite with real and synthetic media — 47 passed, 0 failed, 0 skipped in 17.13 s.
- Final static verification — Ruff check passed; Ruff format check reported 39 files formatted; `compileall` passed.
- Final generated-artifact CLI verification — dependency preflight passed with no warnings; idempotent `generate-edl` reported 4 segments/3 switches/18.000 s; strict `validate` passed.
- Final repository consistency — source structure inspected, Git status inspected, `git diff --check` passed, and input/output media ignore rules were confirmed.
- Approved-footage discovery: 10 files reported, 7 usable likely sources, 3 excluded likely derived outputs; selected conservative event group is `camera_04` / `camera_06`.
- Approved-footage sync assistance: shared audio transient suggestions at 4.270 s and 4.850 s, correlation confidence 0.739, calculated provisional offset +0.580 s. These are not verified claps.
- Approved-footage 90-second preparation: `INSUFFICIENT_COMMON_DURATION`; maximum honest normal output 30.985 s; no EDL or draft fabricated for that request.
- Approved-footage smoke preparation: `READY_FOR_SMOKE_ONLY`; generated project/sync/EDL all passed the existing serialized validation pipeline.
- Approved-footage automatic smoke render: `DRAFT_RENDERED_WITH_UNVERIFIED_SYNC`; 18.000 s, H.264/AAC, 1280x720, 30 fps, SHA-256 `4E0F278DDB58007C064B3DCE77550D7D5773363AF2178A4B204C1EC735AED7D4`.
- Synthetic automatic integration: 1 passed in 7.82 s. Two temporary 92-second sources contained a known 300 ms transient offset; automatic discovery, sync analysis, 90-second EDL, real FFmpeg fallback rendering, output validation, evidence, and final-approval prevention passed. Synthetic data contained no real individuals and was deleted with its temporary directory.
- The first real `inspect` run exposed Windows locale decoding of a non-ASCII filename. FFprobe text capture now forces UTF-8 with replacement, and a regression test passes.
- The first idempotent auto rerun exposed JSON tuple/list comparison differences. Generated JSON comparison now normalizes through JSON representation before deciding whether content differs.

### Evidence-based grouping verification (2026-07-26)

- Real discovery: 10 files total; 7 eligible likely sources; 3 obvious derived outputs excluded; all 21 eligible pairs analyzed.
- Real automatic result: `CAMERA_GROUP_CONFIRMED`, high confidence, selected `camera_02` (`VID20260619151534.mp4`), `camera_04` (`VID_20260619_151529.mp4`), and `camera_05` (`VID_20260619_151532 1.mp4`). The selected group's minimum pair score is 0.844456.
- Strongest real pair: `camera_02/camera_04`, score 0.872776, audio correlation 0.836443, estimated offset +1.960 s, offset stability 0.953343, two shared transient matches. The previously demonstrated `camera_04/camera_06` pair was also supported (score 0.856908, correlation 0.795465, +0.580 s) but was not hardcoded as the winner.
- Real sync suggestions: `camera_02` 2.310 s (0.794), `camera_04` 4.270 s (0.794), `camera_05` 1.470 s (0.771), all `shared_audio_transient`, all requiring human verification, none represented as a verified clap.
- Real auto render: `DRAFT_RENDERED_WITH_UNVERIFIED_SYNC`; MoviePy; 18.000 s; H.264/AAC; 1280×720; 30 fps; 3 camera switches; SHA-256 `7db5cf4d202ae7360963e03e0537c78e57fd3548272bccc00170c1f8c734f377`.
- Automatic summary confirms `human_review_required: true` and `final_approval_performed: false`; the `smoke` and `unverified-sync` filename makes the draft ineligible for final approval. No file was created under `output/final`.
- Synthetic media result: A/B with unrelated filenames and known 300 ms offset were selected; unrelated C was rejected; an `automatic_final.mp4` copy was excluded; generated project/sync/EDL, 90-second FFmpeg fallback draft, output validation, evidence, and non-approval passed. Fixtures contained no real individuals and were deleted with the temporary directory.

### Configurable closing-credit verification (2026-07-27)

- Default generated text is `Edited by the Project Team`; smoke omission retains a one-second credit, while normal omission retains four seconds.
- Custom text is trimmed and serialized exactly; custom duration is used by the generated typed configuration and render plan.
- Blank text and zero, negative, NaN, or infinite durations fail with actionable `PreparationError` messages before media discovery.
- Synthetic automatic integration passes `Edited by Synthetic Team | BTIS3053` and a three-second duration through generated JSON into the FFmpeg fallback render plan; its 90-second rendered output and evidence validate.
- Real automatic MoviePy rendering produced the requested four-second credit screen. Generated project JSON, render evidence, FFprobe, and a sampled closing frame independently confirm the result.
- Real output: `DRAFT_RENDERED_WITH_UNVERIFIED_SYNC`; 20.000 s; SHA-256 `1050763ae5ba81f2c81981bd47c710432f78b348c2e978414d529ce8acd55ac5`; review still required; final approval not performed.
- Exact-byte approval integrity remains covered by integration: promoted final bytes equal the reviewed draft bytes. `src/review.py` was not modified.

### Guided UI verification (2026-07-29)

- Baseline before UI changes: bundled Python `python -m pytest -q` — 58 passed, 4 skipped.
- FastAPI dependencies installed from `requirements.txt`; FastAPI 0.140.13, Uvicorn 0.52.0, and HTTPX 0.28.1 were used locally.
- Targeted API foundation: `python -m pytest backend/tests/test_api_foundation.py -q` — 4 passed, 1 external TestClient deprecation warning.
- Final ordinary Python suite: `python -m pytest -q` — 62 passed, 5 skipped in 0.87 s; four existing media tests and one new UI media integration are opt-in.
- Final Python static verification: `python -m ruff check backend src tests`, `python -m ruff format --check backend src tests`, and `python -m compileall -q backend src tests` — all passed; 58 files formatted.
- Frontend dependency install: `npm install` — 344 packages installed initially; lock file recorded. Production audit currently reports two high advisories in React Router server/RSC behavior; the client-only SPA does not enable RSC or server actions and uses the newest tested 7.18.2 release.
- Frontend tests: `npm test` — 9 passed across 8 test files.
- Frontend quality: `npm run lint`, `npm run format:check`, and `npm run build` — all passed; Vite production build transformed 1,735 modules and emitted a 388.01 kB JavaScript bundle (122.66 kB gzip).
- Real UI API integration, first run: `PIPELINE_UI_INTEGRATION=1 python -m pytest backend/tests/test_ui_pipeline_integration.py -q` — 1 passed in 102.94 s.
- Real UI API integration after approval/persistence hardening: same command — 1 passed in 92.62 s.
- Real UI draft: `output/draft/guided-ui-integration-unverified-sync-smoke_draft.mp4`; 18.000 s, H.264/AAC, 1280×720, 30 fps, SHA-256 `6faa388f667e5751d7fd2678ba8c90b46bb2198993132afabb83d6a23614c37d` on the first recorded probe. The repeated run again passed output validation.
- Real UI result: approved footage was discovered/grouped, transient suggestions remained `needs_human_confirmation`, EDL validation passed, evidence was registered, and both approval eligibility and the approval operation rejected the smoke/unverified draft.
- Local FastAPI and Vite development servers started successfully; health returned HTTP 200 and Vite served the application. The servers were stopped after checks.
- Browser visual automation was attempted through the required in-app browser skill but could not initialize because the environment denied the browser runtime read access to `C:\Users\User\AppData`. No browser screenshot or manual responsive visual claim is made; production build and jsdom component tests passed.
- The desktop runtime removed its initially bundled test packages during the final pass. Dependencies were restored under ignored `temp/python-packages`; the final command used `PYTHONPATH` plus dedicated ignored `temp/pytest-final-base` because the managed environment also denied the system pytest temp directory. Final result: 62 passed, 5 skipped in 0.79 s; Ruff check/format, compileall, `git diff --check`, and FastAPI OpenAPI generation (26 paths) passed.

### Synchronisation regression verification (2026-07-29)

- Targeted Python regression: 27 passed, 0 failed, 0 skipped.
- Final ordinary Python suite: 67 passed, 0 failed, 5 skipped in 1.52 seconds. The skips are opt-in media integrations; real current-footage rendering was executed separately. Warnings were Starlette's existing TestClient/httpx deprecation and an environment-only pytest cache write denial.
- Python Ruff check, Ruff format check, and compileall: passed; 58 files formatted.
- Frontend Vitest: 10 passed, 0 failed across eight files. ESLint and Prettier check passed.
- Frontend TypeScript/Vite production build: passed after redirecting output to ignored `temp/frontend-regression-build-final2`; 1,735 modules transformed.
- Real four-source discovery/grouping: four discovered, zero derived exclusions, four usable, six pairs analysed, Camera2/Camera4 selected at score 0.722232 (`medium`, `CAMERA_GROUP_SUGGESTED`).
- Real alignment: Camera2 anchor 3.290 seconds, Camera4 anchor 42.930 seconds, offset +39.640 seconds, correlation 0.825633, stability 1.0, three agreeing windows, full 43.050-second overlap of the shorter source. State remains `needs_human_confirmation` and is not a verified clap.
- Real insufficient-duration result: normal 120-second request stopped at maximum honest output 51.050 seconds for the automatically selected pair. The raw two-longest-source upper bound including normal presentation screens is approximately 105.106 seconds, so 120 seconds is physically impossible regardless of cue selection.
- Real smoke integration: one 20.000-second MoviePy draft rendered with H.264 video, AAC audio, 1280x720 at 30 fps, three switches, SHA-256 matching evidence, and `DRAFT_RENDERED_WITH_UNVERIFIED_SYNC`. The filename contains `unverified-sync-smoke`, final approval was not called, and existing approval policy rejects it.

### Coverage-duration diagnostic (2026-07-29)

- Generator calculation: `common_usable_timeline` returned 2.800–7.240 seconds and `maximum_honest_output_duration` returned 12.440 seconds for the four-camera UI configuration.
- Per-camera master coverage under those configured offsets: Camera1 0.000–125.109; Camera4 2.800–99.906; Camera3 -45.810–49.903; Camera2 -35.810–7.240 seconds.
- In-memory EDL result: seven contiguous 16-second shots over master 0.000–112.000, alternating Camera1/Camera4, passed `validate_edl` and `build_render_plan`; final expected duration was 120.000 seconds.
- Assigned Camera4 source intervals were 13.200–29.200, 45.200–61.200, and 77.200–93.200 seconds, all within its 97.106-second source. Camera1 covered the remaining intervals within its 125.109-second source.
- Conclusion: the original 12.440-second automatic rejection is a false feasibility rejection caused by all-camera intersection. Render planning and output validation already implement the correct per-segment model.

### Coverage-based renderability verification (2026-07-29)

- Exact regression: the four configured coverage intervals produce 4.440 seconds common overlap and 170.919 seconds total event union. The generator produced a 112-second main EDL (120 seconds including title/credits), with at least three switches; `validate_edl` and `build_render_plan` both passed.
- Disconnected-union regression: two separate 50-second covered components report 100 seconds total event coverage but only 58 seconds maximum renderable output, proving union length is not substituted for continuous renderability.
- Failure regression: a request above calculated maximum renderability raises `PreparationError` with the maximum renderable duration and limiting source details.
- Full Python suite: 70 passed, 0 failed, 5 skipped in 1.31 seconds. Skips are opt-in media workflows.
- Backend API subset: 4 passed, 0 failed, 1 skipped. Analysis schemas expose all three fields; the opt-in real UI media test was not repeated in this change.
- Frontend: 10 passed, 0 failed across 8 files. Tests cover three-metric analysis/review/evidence displays and target-versus-renderable warning behavior.
- Python static verification: Ruff check passed, Ruff format check passed for 58 files, and compileall passed.
- Frontend static verification: ESLint, Prettier, TypeScript, and Vite production build passed; 1,736 modules transformed.
- Approved footage: 4 discovered/usable, 6 pairs analyzed, Camera2/Camera4 selected at score 0.722232, unverified +39.640-second suggestion. Metrics: overlap 43.050, event coverage 97.106009, maximum renderable output 65.466009. The 120-second request correctly returned `INSUFFICIENT_RENDERABLE_DURATION`; final approval remained false.
- Environment note: the first backend collection attempt failed because current Starlette required missing `httpx2`; dependency was declared/installed. A second attempt hit an inaccessible system pytest temp directory; the recorded repository-local `--basetemp` run passed.

## 8. Known Issues and Limitations

- Browser-level screenshot/responsive inspection was not completed because the required in-app browser runtime could not read its local AppData bootstrap path under the managed filesystem policy. Automated jsdom tests, TypeScript compilation, and the production Vite build passed; a human should still open the local UI at common desktop/mobile widths before submission.
- The compact sync waveform is a clearly labelled placeholder. Candidate verification uses the actual registered local audio/video control; future work may expose decoded low-rate waveform samples from FastAPI.
- `npm audit --omit=dev` reports two high advisories for React Router 7.18.2's server/RSC action path. This Vite application is client-only and does not enable React Server Components, server actions, SSR, or the affected endpoints. Recheck and upgrade when a release resolving the advisory is available without reintroducing older client redirect/XSS advisories.
- Current Starlette uses `httpx2`; it is now declared in `requirements.txt`. The repository-local test temp override is still useful where Windows denies the default pytest temp directory.
- The earlier three-camera 2.310/4.270/1.470-second suggestions, 5.695-second landmark, ten-file inventory, and under-26-second duration statement are retained above as historical results for a prior input set. They do not describe the four files currently under `input/`.
- `config/generated_project.json` and `config/generated_sync.json` now record the blocked 120-second Camera2/Camera4 verification run. `edl/generated_editing_decisions.json` remains the prior 20-second smoke EDL and was not selected or rendered by the blocked run; manual project files remain unchanged.
- Pairwise grouping now analyses up to 120 seconds and rejects alignments preserving less than 60% of the shorter source. It still assumes one constant offset; repetitive program audio, heavy noise reduction, clock drift, or missing audio can require human camera/cue selection.
- No deliberate clap was reliably identified in the current footage. The +39.640-second Camera2/Camera4 value is a stable shared-audio alignment suggestion, not a semantically verified clap.
- The current retained smoke draft is 20 seconds and therefore cannot satisfy the 60–180 second submission duration.
- Current raw duration is no longer universally below 60 seconds: Camera1, Camera3, and Camera4 exceed 95 seconds. The exact four-camera regression is structurally renderable at 120 seconds, and the corrected generator now proves it in tests. The automatically selected Camera2/Camera4 pair still supports only 65.466 seconds of output under its current offsets.
- `maximum_honest_output_duration` remains only as a source-compatibility function wrapper; it now returns the coverage-aware maximum renderable duration. New code uses `calculate_duration_metrics` directly.
- The downloaded FFmpeg/FFprobe verification build is ignored under `temp/` and is not a portable repository dependency. Each user must install FFmpeg/FFprobe or provide executable paths.
- Synchronisation uses one constant offset per camera and does not correct clock drift.
- Technical tests confirm title/credit/overlay/transition filters rendered and outputs probe correctly, but only human playback can confirm perceptual readability, audio continuity, content quality, and clap accuracy for real footage.
- FFmpeg font discovery depends on the local build/system. The integration build rendered successfully but emitted non-fatal fontconfig cache warnings before the filter defect was fixed; the final render itself passed.
- The project intentionally has no camera-selection machine learning, face recognition, identity analysis, emotion analysis, cloud upload, autonomous approval, or publication.
- Existing changes are uncommitted; no commit was requested.

## 9. Blockers and Unresolved Questions

- Resolved defect: Automatic duration feasibility no longer equates all-camera overlap with renderability. The accepted implementation and consequences are recorded in ADR 0001 and the verification section above.
- Blocker for compliant real-footage submission: No deliberate clap is reliably identifiable in the selected recordings.
  - Why it matters: The PRD requires manual clap synchronization and ±100 ms verification.
  - Work already attempted: Full-recording envelope correlation, overlap-aware lag ranking, multi-window stability, six-pair diagnostics, and an unverified smoke render. Camera2/Camera4 gives the strongest stable alignment; Camera1/Camera4 is the more useful long-pair alternative but remains below the stronger large-offset correlation threshold.
  - Recommended next action: Listen/view Camera2 near 3.290 seconds against Camera4 near 42.930 seconds, and inspect Camera1/Camera4 around the ranked -17.780-second relationship. Use `confirm-sync` only if the same deliberate cue is unambiguous.
  - Whether other work can continue: Software work and non-acceptance smoke testing are complete; manual clap acceptance and final compliant approval cannot be automated honestly.
- Question: Should the lecturer enforce 60–80 seconds instead of 60–180?
  - Why it matters: It narrows the accepted final duration.
  - Work already attempted: Implemented a configurable policy; default follows the explicit 60–180 instruction.
  - Recommended next action: If confirmed, set `duration_policy.max_seconds` to `80`.
  - Whether other work can continue: Yes.
- Question: What retention period applies to the approved local footage?
  - Why it matters: The user authorised academic local use but did not specify deletion timing.
  - Work already attempted: Kept all media ignored, local, and read-only.
  - Recommended next action: Record the lecturer/team retention decision before submission cleanup.
  - Whether other work can continue: Yes.
- Question: Is a separate demo recording required?
  - Why it matters: It may be a submission deliverable but does not change pipeline code.
  - Work already attempted: Documented the complete CLI workflow.
  - Recommended next action: Confirm with the lecturer and record the demo locally if required.
  - Whether other work can continue: Yes.

## 10. Next Actions

1. Human-review Camera2 near 3.290 seconds against Camera4 near 42.930 seconds; confirm only if the same deliberate clap is unambiguous.
2. If a compliant real draft is required, select a human-verified camera group whose calculated maximum renderable duration meets the requested target; the current automatic Camera2/Camera4 group cannot reach 120 seconds.
3. Run the opt-in real UI media integration after any sync/group change and complete full perceptual playback/privacy/licensing review.
4. Complete the remaining human browser visual/responsive pass and record the footage/evidence retention decision.

## 11. How to Resume

1. Read `PRD_AI_Assisted_Multi_Camera_Kindergarten_v2.md`.
2. Read `architecture.md`.
3. Read `handoff.md`.
4. Inspect `git status` and `git diff`.
5. Run `python -m pytest -q` and `python -m ruff check backend src tests` for the Python baseline; media tests explain their opt-in environment variables.
6. In `frontend/`, run `npm test`, `npm run lint`, `npm run format:check`, and `npm run build`.
7. Start FastAPI and Vite with the exact README PowerShell commands when UI work or manual playback remains.
8. Start from the first applicable item under Next Actions.

## 12. Final Acceptance Checklist

- [x] At least two local camera inputs supported
- [ ] Manual clap offsets calculated (stable shared-audio offsets are provisional; no deliberate clap is verified)
- [x] EDL loaded and validated
- [x] At least two cameras required
- [x] At least three switches required
- [x] Opening title rendered
- [x] Closing credits rendered
- [x] Lower-third, label, or subtitle rendered
- [x] At least one transition rendered
- [x] Draft MP4 exported (latest approved-footage unverified-sync smoke draft is 20 seconds)
- [ ] Approved-footage output duration validated as 60–180 seconds (requires a human-verified long-camera pair; 120 seconds is impossible with current raw durations)
- [x] Synchronisation evidence recorded with unconfirmed-clap status
- [x] MoviePy renderer implemented
- [x] FFmpeg fallback implemented
- [x] Human review record implemented
- [x] Approval bound to SHA-256
- [x] Approved final output separated from draft
- [x] Unit tests passing
- [x] Integration tests passing
- [x] README completed
- [x] Privacy and licensing limitations documented

### Automatic Preparation Acceptance

- [x] `inspect` discovers recursive source videos
- [x] Camera IDs are stable and obvious generated outputs are excluded
- [x] All eligible pairs receive local multi-signal audio/metadata analysis; filename equality is not required
- [x] Filename timestamps normalize separated, compact, prefixed, and Unicode formats
- [x] Pair evidence records correlation, offset, stability, shared transients, score, confidence, and reason
- [x] Best supported pair/group selection and stable tie-breaking are deterministic
- [x] Unrelated audio and likely derived duplicates are rejected
- [x] Repeated `--camera-file` provides a validated explicit-selection fallback
- [x] Generated project configuration is valid and separate from manual config
- [x] Sync assistant produces ranked deterministic candidates and supporting metrics
- [x] Low-confidence/no-audio results do not invent timestamps
- [x] Cross-camera synthetic offset recovery verified
- [x] Human sync confirmation command and state implemented
- [x] Deterministic EDL generation satisfies switches, boundaries, continuity, transition, overlay, and reason rules
- [x] Insufficient duration fails truthfully with maximum renderable duration
- [x] Explicit smoke preparation/rendering is labelled and approval-ineligible
- [x] `prepare` validates serialized generated artefacts and stops before rendering
- [x] `auto` renders a draft, validates output/evidence, and never approves
- [x] Approved-footage discovery, sync analysis, insufficient-duration report, and smoke render executed
- [x] Synthetic 90-second automatic end-to-end workflow executed successfully
- [x] Synthetic same-event A/B, unrelated C, and derived-copy grouping/render workflow executed successfully
- [x] `prepare` and `auto` accept custom credit text and duration
- [x] Omitted credit text defaults to `Edited by the Project Team`
- [x] Visible credit text contains no human-review warning
- [x] Generated credit values are validated, serialized, and rendered
- [x] Closing-credit screen remains mandatory
- [x] Approval still promotes the exact reviewed SHA-256 without modification or rerendering
- [x] README and architecture document the Automatic Preparation Layer
- [x] Correlation ranking rejects tiny-overlap edge maxima
- [x] Multi-window offset alternatives, stability, and preserved-overlap evidence recorded
- [x] Large or overlap-destroying manual timestamps require explicit risk acknowledgement
- [x] Physically usable low-confidence pairs remain ranked human-verification suggestions
- [x] CLI and UI expose **Continue with Human Verification** without weakening downstream validation
- [x] Exact former 12.440-second four-camera regression now generates a valid 120-second coverage-aware EDL in tests
- [x] Real current-footage 120-second failure and 20-second smoke success executed and recorded
- [x] Common overlap versus renderable coverage defect diagnosed with a 120-second in-memory proof
- [x] Three-metric overlap/event-coverage/renderability feasibility implemented
- [x] Interval-aware automatic EDL camera assignment implemented
- [x] API, evidence, CLI, and UI expose all three duration metrics
- [x] `INSUFFICIENT_RENDERABLE_DURATION` replaces the misleading common-duration state

### Guided UI Acceptance

- [x] FastAPI health, preflight, project, job, analysis, sync, EDL, render, review, approval, evidence, and file endpoints implemented
- [x] OpenAPI documentation loads and lists the required route families
- [x] Existing Python modules are invoked directly; CLI subprocess orchestration is not used
- [x] React/TypeScript/Vite/Tailwind/shadcn-style frontend builds
- [x] Six-step persistent workflow stepper and routing implemented
- [x] Project setup persists title, input, duration, resolution, draft/smoke mode, and credits
- [x] Camera inventory, exclusions, selected/master camera, confidence, and pair evidence displayed
- [x] Automatic camera selection and explicit human selection fallback supported
- [x] Sync candidates, offsets, confidence, cue type, verification, confirm, adjust, reject, and local preview supported
- [x] Simplified EDL timeline, reasons, transitions, overlay, limited edits, and validator reuse implemented
- [x] Draft player, render status, output metadata, renderer, sync, and compliance displayed
- [x] Persistent review checklist, reviewer, comments, and decision implemented
- [x] Smoke, unverified sync, invalid duration, incomplete review, filename, and changed-SHA blockers explained
- [x] Approval delegates to exact-checksum promotion and never rerenders
- [x] Evidence inventory supports expand JSON, copy path, and download
- [x] Exact approved job states and one-second polling implemented
- [x] Frontend tests, production build, Python API tests, and real API smoke integration pass
- [ ] Human browser screenshot/responsive QA completed (environment browser bootstrap was denied AppData read access; manual pass remains)
