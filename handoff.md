# Project Handoff

## 1. Project

- Name: AI-Assisted Multi-Camera Kindergarten Graduation Video Editing Pipeline
- Current branch: `main`
- Repository path: `C:\Newfolder\SPI_project\SPI_project`
- Primary documents: `PRD_AI_Assisted_Multi_Camera_Kindergarten_v2.md`, `architecture.md`
- Last updated: 2026-07-26

## 2. Current Status

- Current milestone: Evidence-based Automatic Multi-Camera Grouping
- Overall status: Automatic grouping and the one-command workflow are complete and verified; approved footage remains smoke-only because it is short and has no verified clap
- Last completed task: Completed real-footage 21-pair grouping/auto smoke and a synthetic relevant/unrelated/derived-source 90-second integration render
- Task currently in progress: None
- Next recommended task: Human-review the reported sync regions or supply longer multi-camera footage with a deliberate clap for the academic final

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
- `src/main.py` — CLI-only orchestration and non-zero expected-failure exit status.
- `tests/unit/` — validation, sync, EDL, render plan, FFprobe, renderer adapter, FFmpeg command, examples, and review tests.
- `tests/integration/test_pipeline.py` — real MoviePy render, deliberate real FFmpeg fallback, 72-second contract render, output probing, evidence, and approval workflow.
- `handoff.md` — this implementation and verification record.

- `src/video_discovery.py` — deterministic recursive discovery, exclusions, probing, stable IDs, reports, and conservative related-camera grouping.
- `src/camera_grouping.py` — deterministic multi-signal pair scoring, cached audio analysis, offset/stability/transient evidence, derived-copy detection, confidence states, and best-group selection.
- `src/sync_assistant.py` — local FFmpeg audio-window decoding, transient/correlation analysis, ranked candidates, confidence policy, and human confirmation.
- `src/edl_generator.py` — synchronized common-duration calculation and validated deterministic EDL proposals.
- `src/auto_pipeline.py` — generated project configuration, preparation outcomes, summary evidence, and safe auto-draft orchestration.
- `tests/unit/test_video_discovery.py`, `test_sync_assistant.py`, `test_edl_generator.py`, `test_auto_pipeline.py` — focused automation tests.
- `tests/unit/test_camera_grouping.py`, `test_preflight.py`, `test_media_probe.py` — grouping signals/selection, local executable resolution, and creation-time metadata coverage.
- `tests/integration/test_pipeline.py` — opt-in synthetic compliant automatic workflow with generated temporary media.
- `README.md`, `architecture.md` — automatic, assisted, expert, confidence, smoke, outcome-state, and privacy documentation.
- `config/generated_project.json`, `config/generated_sync.json`, `edl/generated_editing_decisions.json` — latest three-camera real-footage automatic smoke artifacts with automation provenance and unverified synchronization.
- `evidence/reports/camera_grouping.json` — ignored local all-pair grouping evidence; 21 real pairs with signals, scores, offsets, confidence, and reasons.
- `output/draft/kindergarten-graduation-demo-unverified-sync-smoke_draft.mp4` — ignored local 18-second real automatic draft; never promoted or approved.

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

## 5. Architecture and Implementation Decisions

- Decision: The Automatic Preparation Layer is additive and feeds the existing strict pipeline.
  - Reason: Existing validation, render planning, atomic promotion, evidence, review, and checksum approval are working safety boundaries.
  - Consequences: Generated JSON is reloaded through `prepare_pipeline`; validators were not weakened.
  - Affected files: `src/auto_pipeline.py`, `src/edl_generator.py`, `src/main.py`.
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

## 8. Known Issues and Limitations

- Current automatic sync suggests 2.310 s / 4.270 s / 1.470 s for the selected three-camera group; the earlier manual pair inspection recorded a provisional 5.695 s / 5.695 s shared landmark. None is a verified deliberate clap. This disagreement requires human audio/visual review and remains explicit in evidence.
- `config/generated_project.json`, `config/generated_sync.json`, and `edl/generated_editing_decisions.json` currently represent the 18-second three-camera unverified-sync smoke workflow; manual files remain unchanged.
- Pairwise grouping uses only the first 45 seconds of low-rate audio and assumes a constant bounded offset. Repetitive music, heavy noise reduction, severe drift, or missing audio can still cause rejection or require explicit human camera selection.
- Audio correlation assumes a constant offset within the analysed window and does not correct clock drift.

- Approved footage is present under ignored `input/` and the selected pair is mapped in `config/project.json`.
- The canonical `python -m src.main validate` correctly fails because the 64-second main EDL exceeds every available camera duration. This cannot be repaired without longer footage or a lecturer-approved scope change.
- No deliberate clap was reliably identified. The 5.695-second shared landmark is provisional smoke-test evidence and must not be reported as a verified clap.
- The retained smoke draft is 18 seconds and therefore cannot satisfy the 60–180 second submission duration.
- The downloaded FFmpeg/FFprobe verification build is ignored under `temp/` and is not a portable repository dependency. Each user must install FFmpeg/FFprobe or provide executable paths.
- Synchronisation uses one constant offset per camera and does not correct clock drift.
- Technical tests confirm title/credit/overlay/transition filters rendered and outputs probe correctly, but only human playback can confirm perceptual readability, audio continuity, content quality, and clap accuracy for real footage.
- FFmpeg font discovery depends on the local build/system. The integration build rendered successfully but emitted non-fatal fontconfig cache warnings before the filter defect was fixed; the final render itself passed.
- The project intentionally has no camera-selection machine learning, face recognition, identity analysis, emotion analysis, cloud upload, autonomous approval, or publication.
- Existing changes are uncommitted; no commit was requested.

## 9. Blockers and Unresolved Questions

- Blocker: Approved source duration is insufficient for the mandatory full draft.
  - Why it matters: Every approved file is shorter than 26 seconds. The selected synchronized pair has 22.984778 seconds of common footage; with normal four-second title and credits the maximum honest output is 30.984778 seconds, below the 60-second minimum.
  - Work already attempted: Probed all ten files, selected the longest suitable complementary pair, validated the full plan, and confirmed exact boundary failures.
  - Recommended next action: Supply at least 60 seconds of overlapping two-camera footage, or obtain lecturer approval for a shorter output and update the duration policy.
  - Whether other work can continue: Smoke rendering and software testing are complete; the compliant full render cannot continue.
- Blocker: No deliberate clap is reliably identifiable in the selected recordings.
  - Why it matters: The PRD requires manual clap synchronization and ±100 ms verification.
  - Work already attempted: Audio-envelope correlation, transient analysis, full waveforms/spectrograms, and frame samples at 0.0–3.0 s, 5.3–6.1 s, and 14.1–15.1 s.
  - Recommended next action: Human-listen to those exact regions. If no clap is audible, use replacement footage containing a deliberate clap or obtain lecturer approval for a documented shared-audio-cue method.
  - Whether other work can continue: The provisional zero-offset smoke workflow is complete; clap acceptance cannot.
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

1. Human-review the selected files at the automatic shared-transient suggestions: `VID20260619151534.mp4` near 2.310 s, `VID_20260619_151529.mp4` near 4.270 s, and `VID_20260619_151532 1.mp4` near 1.470 s. Compare the earlier 5.695 s landmark on the former manual pair; use `confirm-sync` only if a deliberate clap is unambiguous.
2. Obtain at least 60 seconds of overlapping footage from two cameras with a deliberate clap, or obtain written lecturer approval for the shorter duration and alternate cue.
3. If longer footage is supplied, update only camera paths and verified clap timestamps, then rerun the canonical `python -m src.main validate`.
4. Render the 60–180 second draft only after canonical validation passes.
5. Watch the full draft, complete the checklist, record review, and promote only the unchanged approved SHA-256.
6. Record the agreed footage/evidence retention period and clean local temporary inspection files at the authorised time.

## 11. How to Resume

1. Read `PRD_AI_Assisted_Multi_Camera_Kindergarten_v2.md`.
2. Read `architecture.md`.
3. Read `handoff.md`.
4. Inspect `git status` and `git diff`.
5. Run `python -m pytest -q` for the normal baseline; media tests explain their opt-in environment variables.
6. Run `python -m ruff check src tests`.
7. Start from the first applicable item under Next Actions.

## 12. Final Acceptance Checklist

- [x] At least two local camera inputs supported
- [ ] Manual clap offsets calculated (shared 5.695-second speech cue is provisional, not a verified clap)
- [x] EDL loaded and validated
- [x] At least two cameras required
- [x] At least three switches required
- [x] Opening title rendered
- [x] Closing credits rendered
- [x] Lower-third, label, or subtitle rendered
- [x] At least one transition rendered
- [x] Draft MP4 exported (18-second approved-footage smoke draft)
- [ ] Approved-footage output duration validated as 60–180 seconds (blocked by source duration)
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
- [x] Insufficient duration fails truthfully with maximum honest duration
- [x] Explicit smoke preparation/rendering is labelled and approval-ineligible
- [x] `prepare` validates serialized generated artefacts and stops before rendering
- [x] `auto` renders a draft, validates output/evidence, and never approves
- [x] Approved-footage discovery, sync analysis, insufficient-duration report, and smoke render executed
- [x] Synthetic 90-second automatic end-to-end workflow executed successfully
- [x] Synthetic same-event A/B, unrelated C, and derived-copy grouping/render workflow executed successfully
- [x] README and architecture document the Automatic Preparation Layer
