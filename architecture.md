# Architecture: AI-Assisted Multi-Camera Kindergarten Graduation Video Editing Pipeline

## 1. Document Purpose

This document defines the software architecture for the prototype described in `PRD_AI_Assisted_Multi_Camera_Kindergarten_v2.md`.

It is written to guide implementation by human developers and coding agents such as Codex. It defines:

- system boundaries;
- component responsibilities;
- data contracts;
- processing flow;
- validation rules;
- error-handling behaviour;
- testing boundaries;
- privacy and security controls;
- implementation order.

This is a **local, semi-automated, EDL-driven video editing pipeline**. It is not a fully autonomous AI editor and must not be represented as one.

---

## 2. Architectural Goals

The architecture shall support the following outcomes:

1. Load at least two local camera recordings.
2. Synchronise cameras using manually recorded clap timestamps.
3. Read editing decisions from a human-readable JSON EDL.
4. Apply deterministic, rule-based camera selection decisions recorded in the EDL.
5. Render a 60–180 second MP4 containing:
   - at least two camera angles;
   - at least three camera switches;
   - an opening title;
   - a closing credit screen;
   - at least one subtitle, label, or lower-third;
   - at least one simple transition.
6. Keep all editing decisions explainable and reviewable.
7. Require recorded human approval before an output is treated as final.
8. Keep raw footage and processing local by default.
9. Separate validation, synchronisation, EDL handling, rendering, and review responsibilities.
10. Allow FFmpeg to replace MoviePy as the rendering backend without changing the EDL format.

---

## 3. Scope and Constraints

### 3.1 In Scope

- Command-line prototype.
- Local file processing.
- Two to four camera inputs.
- Manual clap timestamp configuration.
- Master-timeline offset calculation.
- JSON-based EDL.
- Rule-based decisions represented in the EDL.
- MoviePy rendering.
- FFmpeg fallback rendering.
- Draft and final output separation.
- Automated validation and test evidence.
- Human review and approval record.

### 3.2 Out of Scope

- Face recognition or child identification.
- Emotion recognition.
- Biometric analysis.
- Cloud processing of real children’s footage.
- Machine-learning-based camera selection.
- Fully autonomous publishing or approval.
- Real-time editing.
- A graphical timeline editor.
- Mobile application.
- Production deployment.
- Advanced colour grading.
- Professional audio mastering.
- Overlapping EDL segments or mandatory crossfades.

### 3.3 Architectural Constraints

- Python is the primary implementation language.
- MoviePy is the primary rendering library.
- FFmpeg is an external runtime dependency and fallback renderer.
- Input footage should be simulated or explicitly approved.
- The minimum prototype uses non-overlapping EDL segments.
- The synchronisation target at the clap verification point is within ±100 ms.
- The system must fail safely and visibly when validation fails.
- A failed or unreviewed render must never be named or marked as final.

---

## 4. Architecture Style

The system uses a **modular pipeline architecture** with a thin command-line orchestration layer.

```text
Local Input Files
       |
       v
Input Discovery and Validation
       |
       v
Synchronisation Configuration and Offset Calculation
       |
       v
EDL Loading and Semantic Validation
       |
       v
Render Plan Construction
       |
       v
Renderer Adapter
   |           |
   v           v
MoviePy      FFmpeg
   |           |
   +-----+-----+
         |
         v
Draft MP4 and Evidence
         |
         v
Human Review and Approval
         |
         v
Approved Final MP4
```

The architecture intentionally separates **what to edit** from **how to render it**:

- The EDL defines what segments and actions are required.
- The synchronisation module maps master-timeline times to source-camera times.
- The render-plan builder produces renderer-neutral instructions.
- A renderer adapter converts those instructions into MoviePy operations or FFmpeg commands.

---

## 5. System Context

### 5.1 Actors

- **Teacher/editor:** prepares inputs, sync timestamps, and EDL decisions.
- **Project team member:** runs the pipeline and resolves validation errors.
- **Human reviewer:** inspects the draft and records approval or requested changes.
- **Lecturer/evaluator:** reviews architecture, code, EDL, evidence, and final output.

### 5.2 External Dependencies

- Local operating-system file system.
- Python runtime.
- MoviePy and its dependencies.
- FFmpeg and FFprobe executables.
- A standard MP4 player for manual review.

### 5.3 Trust Boundary

All raw footage, configurations, intermediate files, and outputs remain inside the local project directory unless a human explicitly moves them. No component is permitted to upload footage or metadata to an external service.

---

## 6. Proposed Repository Structure

```text
kindergarten-video-pipeline/
├── README.md
├── PRD.md
├── architecture.md
├── requirements.txt
├── .gitignore
├── input/
│   └── .gitkeep
├── config/
│   ├── project.json
│   └── sync.json
├── edl/
│   └── editing_decisions.json
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── errors.py
│   ├── logging_config.py
│   ├── validate_inputs.py
│   ├── media_probe.py
│   ├── sync.py
│   ├── edl.py
│   ├── render_plan.py
│   ├── renderer.py
│   ├── moviepy_renderer.py
│   ├── ffmpeg_renderer.py
│   ├── review.py
│   └── evidence.py
├── tests/
│   ├── fixtures/
│   ├── unit/
│   │   ├── test_validate_inputs.py
│   │   ├── test_sync.py
│   │   ├── test_edl.py
│   │   └── test_render_plan.py
│   └── integration/
│       └── test_pipeline.py
├── output/
│   ├── draft/
│   └── final/
├── temp/
└── evidence/
    ├── logs/
    ├── reports/
    ├── screenshots/
    └── approvals/
```

### Repository Rules

- Do not commit real children’s footage.
- Ignore `input/`, `temp/`, rendered media, and local logs where appropriate.
- Keep small simulated fixtures under `tests/fixtures/` only if their use is authorised.
- Store source and licence information for fonts, music, and third-party assets in the report or a licence manifest.

---

## 7. Component Design

## 7.1 CLI Orchestrator: `src/main.py`

### Responsibility

Coordinates pipeline stages without implementing domain logic.

### Proposed Commands

```bash
python -m src.main inspect --input input
python -m src.main detect-sync --input input
python -m src.main generate-edl --config config/generated_project.json --sync config/generated_sync.json --duration 90
python -m src.main prepare --input input --duration 90 --title "Kindergarten Graduation Ceremony"
python -m src.main auto --input input --duration 90 --title "Kindergarten Graduation Ceremony"
python -m src.main validate --config config/project.json --sync config/sync.json --edl edl/editing_decisions.json
python -m src.main render --config config/project.json --sync config/sync.json --edl edl/editing_decisions.json
python -m src.main review --draft output/draft/project_draft.mp4
python -m src.main approve --draft output/draft/project_draft.mp4 --reviewer "Reviewer Name"
```

### Behaviour

1. Parse CLI arguments.
2. Load configuration.
3. Run all validation before expensive rendering.
4. Build a renderer-neutral render plan.
5. Select MoviePy unless the configuration explicitly requests FFmpeg or MoviePy fails with a recoverable backend error.
6. Export only to `output/draft/` during rendering.
7. Generate evidence and checksums.
8. Require a separate approval operation before copying or promoting a file to `output/final/`.

The orchestrator must return a non-zero process exit code on failure.

---

## 7.2 Domain Models: `src/models.py`

Use typed dataclasses or equivalent typed models to prevent unstructured dictionaries from spreading across the codebase.

### Core Models

```python
CameraSource
- id: str
- path: pathlib.Path
- clap_time_seconds: float
- offset_seconds: float
- duration_seconds: float | None
- width: int | None
- height: int | None
- fps: float | None
- has_audio: bool | None

EDLSegment
- id: str
- start: float
- end: float
- camera: str
- reason: str
- action: str
- overlay: OverlaySpec | None

OverlaySpec
- type: str
- text: str
- start: float | None
- end: float | None
- position: str | None

ProjectConfig
- project: str
- master_camera: str
- output_width: int
- output_height: int
- output_fps: int
- renderer: str
- title: TitleSpec
- credits: CreditSpec
- cameras: list[CameraSource]

RenderInstruction
- segment_id: str
- source_path: pathlib.Path
- master_start: float
- master_end: float
- source_start: float
- source_end: float
- camera_id: str
- action: str
- reason: str
- overlay: OverlaySpec | None

ReviewRecord
- project: str
- draft_path: str
- draft_sha256: str
- reviewer: str
- status: str
- comments: str
- reviewed_at: str
```

All time values are represented as floating-point seconds. Internal calculations should preserve millisecond precision.

---

## 7.3 Input Validator: `src/validate_inputs.py`

### Responsibility

Validate files and top-level configuration before synchronisation or rendering.

### Checks

- Project configuration exists and is valid JSON.
- At least two camera sources are configured.
- Camera IDs are unique.
- The master camera exists.
- Every camera path exists and is a regular local file.
- Supported extensions are limited initially to `.mp4`, `.mov`, and `.mkv`.
- Files are readable.
- Title and credit text are non-empty.
- Output settings are positive and supported.
- Required directories can be created or written to.
- No input file path points inside `output/` or `temp/`.

The validator returns a structured list of errors rather than stopping at the first error, where safe to do so.

---

## 7.4 Media Probe: `src/media_probe.py`

### Responsibility

Read technical metadata without decoding the full video.

### Implementation

Use `ffprobe` through `subprocess` and parse JSON output.

### Collected Metadata

- duration;
- video width and height;
- frame rate;
- codecs;
- audio-stream availability.

### Rules

- Reject unreadable or zero-duration videos.
- Warn, but do not necessarily reject, cameras with different resolutions or frame rates.
- Store probe results in the evidence report.
- Never pass untrusted strings through a shell. Use argument arrays with `subprocess.run(..., shell=False)`.

---

## 7.5 Synchronisation Module: `src/sync.py`

### Responsibility

Convert manual clap timestamps into offsets relative to the master camera.

### Offset Formula

For camera `c`:

```text
offset(c) = clap_time(c) - clap_time(master)
```

To extract a segment defined on the master timeline:

```text
source_start(c) = master_start + offset(c)
source_end(c)   = master_end   + offset(c)
```

### Example

If the master clap occurs at `5.0 s` and camera 2's clap occurs at `7.2 s`:

```text
offset(camera2) = 7.2 - 5.0 = 2.2 s
```

A master-timeline segment from `20.0 s` to `30.0 s` maps to camera 2 source time `22.2 s` to `32.2 s`.

### Validation

- Clap timestamps must be numeric and non-negative.
- One configured camera must be the master.
- Master offset must resolve to zero.
- Calculated source times must not be negative.
- Calculated source ends must not exceed probed source duration.
- Computed offsets are written to a synchronisation evidence report.

### Important Limitation

The prototype assumes constant offsets and does not correct clock drift. For short starter videos this is acceptable. Clock-drift correction is future work.

---

## 7.6 EDL Loader and Validator: `src/edl.py`

### Responsibility

Parse and semantically validate the editing decision list.

### EDL Contract

```json
{
  "project": "kindergarten-graduation-demo",
  "timeline": [
    {
      "id": "seg-001",
      "start": 0.0,
      "end": 12.0,
      "camera": "camera1_front_left",
      "reason": "Clear opening view of the stage",
      "action": "fade_in"
    },
    {
      "id": "seg-002",
      "start": 12.0,
      "end": 28.0,
      "camera": "camera2_front_right",
      "reason": "Closer view of the speaker",
      "action": "cut",
      "overlay": {
        "type": "lower_third",
        "text": "Graduation Speech",
        "start": 13.0,
        "end": 17.0,
        "position": "bottom"
      }
    }
  ]
}
```

### Supported Actions

- `cut`
- `fade_in`
- `fade_out`
- `fade_to_black`

### Validation Rules

- Root object contains `project` and `timeline`.
- Timeline is a non-empty list.
- Segment IDs are non-empty and unique.
- Times are numeric.
- `start >= 0`.
- `end > start`.
- Segments are ordered by start time.
- Segments do not overlap.
- Gaps are rejected in the minimum prototype unless explicitly allowed later.
- Camera ID exists in project configuration.
- Reason is non-empty and human-readable.
- Action is supported.
- Total main-footage duration is 60–180 seconds unless title and credit duration are explicitly included in the project’s chosen duration calculation.
- At least two distinct cameras are used.
- At least three camera changes occur.
- At least one supported transition action occurs.
- At least one eligible overlay exists across the project configuration or EDL.

### Camera Switch Counting

A switch occurs when adjacent segments use different camera IDs.

```text
[camera1, camera2, camera1, camera2] = 3 switches
[camera1, camera1, camera2, camera2] = 1 switch
```

---

## 7.7 Optional Rule-Based EDL Assistance

The minimum architecture treats the EDL as an approved input. If the team implements EDL assistance, it must remain deterministic and separate from rendering.

Possible rules include:

- prefer a wide camera for group moments;
- prefer a close camera for speeches;
- reject segments marked unstable or blocked;
- enforce a minimum shot duration;
- avoid immediate repeated switching;
- require a reason for every suggestion.

Any generated EDL is a **proposal** and must be reviewed before rendering. The architecture must not label rule execution as machine learning.

---

## 7.8 Render Plan Builder: `src/render_plan.py`

### Responsibility

Translate validated master-timeline EDL segments into renderer-neutral source instructions.

### Processing

For each EDL segment:

1. Resolve the selected camera.
2. Read the camera offset.
3. Calculate source start and end.
4. Recheck source boundaries.
5. Attach transition and overlay instructions.
6. Append an immutable `RenderInstruction`.

The full plan also contains:

- opening title specification;
- closing credit specification;
- output resolution and frame rate;
- output audio policy;
- expected duration;
- renderer selection.

This layer must not import MoviePy.

---

## 7.9 Renderer Interface: `src/renderer.py`

### Responsibility

Define a stable abstraction for rendering backends.

```python
class Renderer(Protocol):
    def render(self, plan: RenderPlan, output_path: Path) -> RenderResult:
        ...
```

### Render Result

```python
RenderResult
- output_path: pathlib.Path
- backend: str
- started_at: str
- completed_at: str
- duration_seconds: float
- warnings: list[str]
- command_log_path: pathlib.Path | None
```

Rendering backends must not modify the validated EDL.

---

## 7.10 MoviePy Renderer: `src/moviepy_renderer.py`

### Responsibility

Primary renderer for the prototype.

### Rendering Sequence

1. Create opening title clip.
2. Open each required video source.
3. Extract each source interval from the render plan.
4. Resize or pad clips to the configured canvas.
5. Preserve a consistent frame rate.
6. Apply supported transition actions.
7. Add configured text overlay or lower-third.
8. Concatenate clips in EDL order.
9. Add closing credits.
10. Export H.264 video with AAC audio in an MP4 container.
11. Close all media resources in `finally` blocks.

### Audio Policy

- Use the audio from the selected camera segment by default.
- Apply short audio fades at boundaries where needed to reduce clicks.
- Do not mix music unless its licence and source are documented.
- Audio discontinuity is checked during manual review.

### Text Policy

Use a bundled or system font whose licence is recorded. Text must remain readable at the target 720p output resolution.

---

## 7.11 FFmpeg Renderer: `src/ffmpeg_renderer.py`

### Responsibility

Fallback backend when MoviePy fails because of environment, text rendering, memory use, or synchronisation issues.

### Design Rules

- Build commands from validated values only.
- Use `subprocess.run` with argument arrays and `shell=False`.
- Save generated filter graphs or command descriptions to `evidence/logs/`.
- Capture stdout, stderr, return code, and elapsed time.
- Never silently fall back. Record the reason for fallback in evidence.
- Produce the same logical title, credits, overlay, transition, and segment order as the render plan.

### Fallback Trigger

Fallback is allowed when:

- MoviePy raises a renderer-specific recoverable error;
- the user explicitly selects FFmpeg in configuration;
- a preflight check shows MoviePy cannot satisfy a required operation.

EDL or configuration validation failures must not trigger fallback because another renderer cannot correct invalid input.

---

## 7.12 Review Module: `src/review.py`

### Responsibility

Enforce the human-in-the-loop boundary.

### Draft Rules

- Initial renders are saved under `output/draft/`.
- Draft filenames contain `_draft`.
- Rendering alone never creates a final file.

### Review Checklist

The reviewer confirms:

- output opens in a standard video player;
- total duration is 60–180 seconds;
- clap synchronisation is within the selected threshold;
- at least two cameras appear;
- at least three camera switches occur;
- title is present and readable;
- credits are present and readable;
- one lower-third, label, or subtitle is present;
- one transition is visible;
- important moments are retained;
- camera choices are reasonable;
- audio continuity is acceptable;
- no unintended private or identifying information appears;
- music, fonts, and other assets have acceptable licences.

### Approval Behaviour

Approval creates a JSON review record, calculates the draft SHA-256 checksum, and copies or renames the exact reviewed draft into `output/final/`.

If the draft changes after review, its checksum changes and previous approval becomes invalid.

---

## 7.13 Evidence Module: `src/evidence.py`

### Responsibility

Create reproducible technical evidence for the report and evaluation.

### Evidence Outputs

- input metadata report;
- calculated camera offsets;
- EDL validation report;
- camera switch count;
- expected and actual output duration;
- renderer/backend used;
- warnings and errors;
- render execution time;
- output checksum;
- review record;
- software version report.

Evidence files should be machine-readable JSON where practical and may also have a concise text summary.

---

## 8. Configuration Contracts

## 8.1 Project Configuration: `config/project.json`

```json
{
  "project": "kindergarten-graduation-demo",
  "master_camera": "camera1_front_left",
  "renderer": "moviepy",
  "allow_ffmpeg_fallback": true,
  "output": {
    "width": 1280,
    "height": 720,
    "fps": 30,
    "video_codec": "libx264",
    "audio_codec": "aac"
  },
  "title": {
    "text": "Kindergarten Graduation Ceremony",
    "duration": 4.0
  },
  "credits": {
    "text": "Edited by the Project Team",
    "duration": 4.0
  },
  "cameras": [
    {
      "id": "camera1_front_left",
      "path": "input/camera1_front_left.mp4"
    },
    {
      "id": "camera2_front_right",
      "path": "input/camera2_front_right.mp4"
    }
  ]
}
```

## 8.2 Synchronisation Configuration: `config/sync.json`

```json
{
  "master_camera": "camera1_front_left",
  "clap_timestamps": {
    "camera1_front_left": 5.0,
    "camera2_front_right": 7.2
  },
  "verification_threshold_ms": 100
}
```

The `master_camera` value must match in both configuration files.

---

## 9. End-to-End Processing Flow

### Phase A: Preflight

1. Load project configuration.
2. Load sync configuration.
3. Verify local input files.
4. Probe media metadata.
5. Calculate camera offsets.
6. Load and validate the EDL.
7. Build the render plan.
8. Print a human-readable preflight summary.

If any error is present, stop before rendering.

### Phase B: Draft Rendering

1. Create a temporary output filename.
2. Render using MoviePy or selected backend.
3. If an allowed MoviePy backend failure occurs, record it and retry once with FFmpeg.
4. Probe the rendered output.
5. Validate duration and streams.
6. Move the completed file atomically to `output/draft/`.
7. Generate evidence.

A partial file must remain in `temp/` and must never be promoted as a draft.

### Phase C: Human Review

1. Reviewer watches the whole draft.
2. Reviewer completes the checklist.
3. If corrections are required, update the EDL or configuration and render a new draft.
4. If accepted, record approval against the draft checksum.
5. Promote only the approved binary to `output/final/`.

---

## 10. Error Handling

## 10.1 Error Categories

```text
ConfigurationError
InputFileError
MediaProbeError
SyncValidationError
EDLParseError
EDLValidationError
RenderPlanError
MoviePyRenderError
FFmpegRenderError
OutputValidationError
ReviewError
ApprovalError
```

## 10.2 Error Principles

- Errors must identify the file, field, or segment involved.
- User-facing messages must suggest the next corrective action.
- Stack traces are written to logs but are not the only user-facing output.
- Invalid inputs stop the pipeline before rendering.
- Renderer errors do not erase the original EDL or source files.
- Partial outputs are not treated as successful.
- No exception may automatically approve or publish a video.

### Example Error

```text
EDLValidationError: Segment 'seg-004' references unknown camera
'camera3_wide_back'. Configured cameras are:
[camera1_front_left, camera2_front_right].
```

---

## 11. Logging and Observability

Use Python's standard `logging` module.

### Log Levels

- `INFO`: pipeline stage, selected backend, source metadata, output location.
- `WARNING`: non-blocking media mismatch, fallback activation, optional feature skipped.
- `ERROR`: validation or rendering failure.
- `DEBUG`: calculated time mappings and backend details, disabled by default.

### Privacy Rules for Logs

- Do not log video frame content.
- Do not copy personal names from footage into logs.
- Use camera IDs and segment IDs.
- Avoid absolute user-home paths in shared evidence where possible.
- Review logs before submission.

---

## 12. Security, Privacy, and Responsible Design

### 12.1 Local-Only Processing

The architecture has no cloud SDK, upload module, remote API, or telemetry requirement. Network access is not needed for normal processing.

### 12.2 Data Minimisation

- Process only the files required by the EDL.
- Store offsets and technical metadata instead of extracted biometric information.
- Avoid creating unnecessary frame snapshots.
- Delete temporary clips after successful completion or failure cleanup.

### 12.3 Access and Retention

- Keep raw footage in a restricted local folder.
- Do not commit footage to a public Git repository.
- Record an agreed deletion date for raw and temporary files.
- Preserve only submission evidence that does not expose children unnecessarily.

### 12.4 Human Accountability

- The EDL reason field makes each camera decision inspectable.
- Rule-based assistance produces suggestions, not approvals.
- Final status requires human review.
- Documentation must distinguish manual work, deterministic automation, and any actual AI component.

### 12.5 Copyright and Licensing

Maintain a dependency and asset licence record covering:

- MoviePy;
- FFmpeg;
- Python packages;
- fonts;
- music;
- visual assets.

No unlicensed background music should be embedded.

---

## 13. Performance and Resource Considerations

This is a short 720p prototype, but rendering can still be resource intensive.

### Controls

- Probe files before decoding.
- Load only cameras referenced by the EDL.
- Close clips and subprocess resources promptly.
- Render through a temporary file.
- Keep output at 1280×720 and 30 fps unless authorised otherwise.
- Avoid unnecessary intermediate re-encoding.
- Provide a lower-resolution test mode for development if needed.

### Test Mode

An optional `--preview` flag may render a short, lower-resolution sample. Preview output must be labelled clearly and cannot satisfy final acceptance criteria.

---

## 14. Testing Architecture

## 14.1 Unit Tests

### Input Validation

- accepts two valid local camera files;
- rejects a missing file;
- rejects duplicate camera IDs;
- rejects an unknown master camera.

### Synchronisation

- calculates positive offsets correctly;
- calculates negative offsets correctly;
- returns zero for the master camera;
- rejects missing clap timestamps;
- rejects negative source extraction times.

### EDL

- loads valid JSON;
- rejects malformed JSON;
- rejects empty reason;
- rejects unknown camera;
- rejects unsupported action;
- rejects overlapping segments;
- rejects invalid time range;
- counts switches correctly;
- enforces two-camera and three-switch minimums;
- enforces duration requirements.

### Render Plan

- maps master times to source times correctly;
- rejects segments outside source duration;
- preserves EDL order and reasons;
- includes title, credits, overlay, and transition instructions.

## 14.2 Integration Tests

- two simulated cameras and a valid EDL produce a draft MP4;
- output contains one video stream and an expected audio stream;
- output duration is within 60–180 seconds;
- selected backend is recorded;
- fallback produces a valid output when deliberately triggered;
- approval promotes only the reviewed checksum.

## 14.3 Manual Acceptance Test

The team must visually and audibly verify:

- clap sync error is no more than ±100 ms;
- title and credits are readable;
- overlay is readable;
- transition is visible;
- at least three camera switches occur;
- audio is understandable;
- no obvious black frames or encoding defects occur;
- content is appropriate and respects consent limits.

---

## 15. Requirement Traceability

| Requirement | Architectural Component |
|---|---|
| FR-01 Load input videos | `validate_inputs.py`, `media_probe.py` |
| FR-02 Read sync data | `sync.py` |
| FR-03 Load and validate EDL | `edl.py` |
| FR-04 Extract segments | `render_plan.py`, renderer backends |
| FR-05 Switch cameras | EDL validator, render plan, renderer |
| FR-06 Opening title | project config, renderer |
| FR-07 Closing credits | project config, renderer |
| FR-08 Subtitle/lower-third | EDL overlay, renderer |
| FR-09 Transition | EDL action, renderer |
| FR-10 Export MP4 | renderer, media probe, evidence |
| FR-11 Human review | `review.py` |
| NFR-01 Explainability | EDL `reason`, evidence report |
| NFR-02 Privacy | local trust boundary and repository rules |
| NFR-03 Local processing | no network component |
| NFR-04 Reliability | validation, typed errors, atomic outputs |
| NFR-05 Reproducibility | config files, README, evidence |
| NFR-06 Maintainability | modular pipeline and renderer interface |
| NFR-07 Honest capability | deterministic EDL assistance and human approval |

---

## 16. Key Architectural Decisions

### ADR-001: Manual Clap Synchronisation

**Decision:** Use manually entered clap timestamps with one master camera.

**Reason:** It is easy to demonstrate, verify, and explain within a prototype.

**Trade-off:** It does not correct clock drift and requires human timestamp entry.

### ADR-002: JSON EDL as the Source of Editing Decisions

**Decision:** Use JSON for the minimum prototype.

**Reason:** JSON is human-readable, machine-parseable, version-controllable, and directly connects decisions to code.

**Trade-off:** It is less convenient than a graphical timeline for non-technical editors.

### ADR-003: Renderer-Neutral Render Plan

**Decision:** Keep EDL parsing and time mapping independent of MoviePy.

**Reason:** This enables an FFmpeg fallback and improves testing.

**Trade-off:** It adds an intermediate model and slightly more code.

### ADR-004: MoviePy Primary, FFmpeg Fallback

**Decision:** Use MoviePy first and FFmpeg as a controlled fallback.

**Reason:** MoviePy is easier to explain in Python, while FFmpeg provides a reliable lower-level alternative.

**Trade-off:** The team must maintain equivalent behaviour across two backends.

### ADR-005: Mandatory Human Approval

**Decision:** Rendering creates a draft only. Final status requires an approval record tied to a checksum.

**Reason:** The system handles sensitive video and may make poor deterministic selections.

**Trade-off:** The workflow cannot be fully unattended.

### ADR-006: No GUI in the Minimum Architecture

**Decision:** Provide a CLI and configuration files only.

**Reason:** The PRD does not require a UI, and a CLI reduces implementation risk.

**Trade-off:** Non-technical users may require assistance editing JSON.

---

## 17. Known Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| MoviePy version or text-rendering failure | Render cannot complete | Preflight dependency check and FFmpeg fallback |
| Incorrect clap timestamps | Visible or audible sync error | Offset report and manual clap verification |
| Camera clock drift | Sync declines later in video | Use short footage; document limitation; future drift correction |
| EDL points outside source duration | Render failure or missing footage | Probe durations and validate mapped intervals before rendering |
| Different resolutions or frame rates | Inconsistent output or resource use | Normalise to configured 720p/30 fps output |
| Audio discontinuity on camera changes | Poor viewing experience | Short audio fades and mandatory manual review |
| Misleading “AI-assisted” claim | Professional and academic integrity issue | Describe implemented method as deterministic, rule-based assistance |
| Sensitive footage enters Git or cloud | Privacy breach | `.gitignore`, local-only design, simulated footage, access controls |
| Unlicensed music or fonts | Copyright/licensing issue | Asset licence manifest and review checklist |
| Assignment document contains unrelated rubric content | Scope confusion | Follow the official project title, main task, deliverables, and lecturer clarification log |

---

## 18. Implementation Sequence for Codex

Coding agents should implement the architecture in small, testable increments.

### Milestone 1: Project Skeleton and Models

- Create repository directories.
- Add typed models and custom exceptions.
- Add sample project, sync, and EDL files.
- Add dependency and executable preflight checks.

### Milestone 2: Validation

- Implement project configuration validation.
- Implement `ffprobe` metadata extraction.
- Implement sync calculation.
- Implement EDL parsing and semantic validation.
- Add unit tests before rendering code.

### Milestone 3: Render Plan

- Implement master-to-source timeline mapping.
- Add boundary checks.
- Produce a printable render-plan summary.
- Add unit tests for positive and negative offsets.

### Milestone 4: MoviePy Draft Renderer

- Add title and credits.
- Extract and concatenate camera segments.
- Add transition support.
- Add one overlay.
- Export draft MP4.
- Ensure resource cleanup.

### Milestone 5: Output Validation and Evidence

- Probe rendered output.
- Verify actual duration and streams.
- Create JSON evidence reports.
- Use temporary files and atomic promotion.

### Milestone 6: FFmpeg Fallback

- Implement equivalent FFmpeg render behaviour.
- Record fallback reason and command evidence.
- Add an integration test that exercises fallback.

### Milestone 7: Human Review

- Implement checklist record creation.
- Calculate SHA-256 checksum.
- Promote an approved draft to final.
- Reject approval if the file changed.

### Milestone 8: Documentation and Final Tests

- Complete README setup and execution instructions.
- Record dependency and asset licences.
- Run unit and integration tests.
- Capture synchronisation and review evidence.

---

## 19. Codex Implementation Rules

When Codex or another coding agent modifies the project, it should follow these rules:

1. Read `PRD.md` and `architecture.md` before editing code.
2. Implement one milestone or narrowly scoped task at a time.
3. Do not add cloud services, facial analysis, or machine-learning claims.
4. Do not change the EDL contract without updating validation, examples, tests, and this document.
5. Keep domain logic outside `main.py`.
6. Do not import MoviePy inside the EDL, sync, or render-plan modules.
7. Validate all inputs before starting a render.
8. Use `pathlib.Path` for paths.
9. Use `subprocess` argument arrays with `shell=False` for FFmpeg and FFprobe.
10. Never overwrite source footage.
11. Never write a rendered file directly to the final directory.
12. Add or update tests for every behaviour change.
13. Keep errors readable and actionable.
14. Preserve reasons and evidence for every editing decision.
15. Do not silently activate fallback behaviour.
16. Clean up media resources and temporary files safely.
17. Keep all processing local.

---

## 20. Definition of Architecture Complete

This architecture is ready for implementation when:

- component boundaries are accepted by the team;
- configuration and EDL contracts are frozen for the first prototype;
- the master camera and clap timestamps can be represented;
- validation rules match the approved PRD;
- MoviePy and FFmpeg responsibilities are clear;
- draft and final output states are separate;
- the human approval mechanism is agreed;
- privacy and local-processing boundaries are understood;
- tests can be mapped to requirements;
- unresolved lecturer questions are recorded rather than guessed.

---

## 21. Open Questions for Lecturer or Team Decision

1. Should the required 60–180 second duration include the opening title and closing credits, or only the main EDL timeline?
2. Will the official starter pack contain two or four usable camera files?
3. Is rule-based EDL creation sufficient for the “automation” component?
4. Must a demo recording be submitted in addition to the final MP4 or repository/ZIP?
5. Should the project implement both rendering backends, or is a documented FFmpeg fallback plan sufficient?
6. Does the unrelated KinderSort/Ollama/Windows-installer rubric apply to this project, or should only the multi-camera project rubric be followed?
7. What retention period should be used if lecturer-approved footage contains identifiable individuals?

Until these questions are answered, implementation should use the conservative defaults documented in this architecture without expanding scope.

---

## 22. Automatic Preparation Layer

The Automatic Preparation Layer sits in front of, and does not replace, the
validated manual pipeline:

```text
Local input directory
        |
        v
Video discovery and safe FFprobe inspection
        |
        v
Pairwise evidence-based camera grouping
        |
        v
Local audio sync-candidate assistant
        |
        v
Deterministic rule-based EDL proposal
        |
        v
Existing validation / render-plan / renderer / evidence pipeline
        |
        v
Draft requiring human review (never automatic approval)
```

### 22.1 Discovery: `src/video_discovery.py`

Discovery recursively considers `.mp4`, `.mov`, and `.mkv` files. It excludes
`output`, `temp`, and `evidence` directories and obvious derived names containing
`draft`, `final`, `rendered`, or `output`, unless the operator explicitly includes
them. Candidate ordering uses normalized relative paths, so `camera_01`,
`camera_02`, and subsequent IDs are stable for the same directory contents.

Every usable candidate is probed through the existing argument-array FFprobe
implementation. The report records duration, stored resolution, display rotation,
frame rate, video/audio codecs, audio availability, classification, and warnings.
Unreadable or zero-duration files remain visible as rejected report entries and
receive no fabricated camera ID.

Filename date/time is normalized when present, including compact, separated,
Unicode-prefixed, `VID`, and `video` variants. It is supporting evidence only:
missing timestamps or hour-scale device time-zone differences do not reject a
pair before local audio analysis.

### 22.2 Camera grouping: `src/camera_grouping.py`

Every eligible two-file combination is analyzed. Each audio stream is decoded
once, locally, to a bounded 8 kHz mono representation and cached, so two to ten
inputs require one decode per source rather than one decode per pair. Grouping
does not decode full-resolution video.

For each pair the component records:

- normalized filename and FFprobe creation-time distance;
- duration compatibility and honest common coverage;
- audio availability and normalized envelope cross-correlation;
- the best bounded time offset;
- shared transient count and strength;
- offset consistency across as many as three audio windows;
- source confidence; and
- a derived-output or near-identical-copy penalty.

The documented score weights are 0.42 audio correlation, 0.13 offset stability,
0.10 shared transients, 0.06 filename time, 0.04 creation time, 0.08 duration
compatibility, 0.08 common duration, 0.04 audio availability, and 0.05 source
confidence. A derived duplicate can subtract 0.80. Audio evidence and sufficient
duration are mandatory: matching filenames, duration, codec, or resolution alone
cannot accept a pair.

The strongest accepted pair anchors selection. A third or fourth source is added
only when every pair relationship is high-confidence and the weakest relationship
is within 0.05 of the strongest pair score. Ties use stable camera IDs. This
prevents a large but weak clique from displacing a better-supported pair while
still allowing coherent three- or four-camera groups.

Obvious generated names remain excluded during discovery. A practical duplicate
check also considers near-identical duration, audio identity at zero offset, and
matching stream characteristics, so a transcoded or copied output is not counted
as an independent camera angle. The complete report is written to
`evidence/reports/camera_grouping.json` with every pair, signal, score, offset,
confidence, and acceptance or rejection reason.

Grouping states are `CAMERA_GROUP_CONFIRMED`, `CAMERA_GROUP_SUGGESTED`,
`CAMERA_GROUP_LOW_CONFIDENCE`, `NO_RELIABLE_CAMERA_GROUP`, and
`DERIVED_OUTPUTS_ONLY`. Medium confidence can support only explicit smoke mode;
low confidence returns `NEEDS_CAMERA_SELECTION` and lists the highest rejected
pairs. Repeated `--camera-file` values provide a fallback selection but bypass
none of probing, sync, duration, EDL, privacy, smoke, or approval controls.

### 22.3 Synchronization assistant: `src/sync_assistant.py`

The assistant decodes only a configurable initial audio window (15 seconds by
default) to 8 kHz mono samples using local FFmpeg. It calculates short-time RMS
energy, robust transient prominence, ranked peak candidates, and cross-camera
envelope correlation. Processing is deterministic and local.

Candidate states are honest:

- `clap_candidate`
- `shared_audio_transient`
- `low_confidence_candidate`
- `no_reliable_candidate`
- `manually_verified_clap`

Automatic candidates always set `requires_human_verification: true`. A correlated
transient is not labelled a verified clap. Below the documented 0.65 confidence
threshold, candidate observations may be saved but no canonical timestamp is
selected. `confirm-sync` records explicit human timestamps; all selected cameras
must be confirmed before the configuration becomes `manual_clap` / `verified`.
The existing constant-offset formula and ±100 ms manual acceptance target remain
unchanged.

Camera grouping confidence establishes only likely shared event content. It does
not prove that a transient is a deliberate clap. Synchronization confidence,
`requires_human_verification`, and the manual ±100 ms acceptance rule remain
separate.

### 22.4 Project and EDL generation: `src/edl_generator.py`

Generated project configuration uses a deterministic master camera, 1280×720 at
30 fps, MoviePy primary rendering, and enabled FFmpeg fallback. Generated files
are separate from manual files and cannot replace different content without
`--overwrite`.

The EDL generator calculates the synchronized common timeline after offsets. It
never creates a source interval outside a probed duration. Normal proposals target
60–180 seconds, use 8-second minimum, 12-second preferred, and 20-second maximum
shots, alternate available cameras, include at least three switches, create
contiguous non-overlapping segments, add a lower-third, start with `fade_in`, end
with `fade_to_black`, and explain every decision.

Generation metadata is stored in a separate report and states that the mechanism
is deterministic rule-based automation, not machine learning. The serialized EDL
is reloaded through the existing EDL validator and render-plan boundary checks.
When duration is impossible, the report identifies the maximum honest duration
and limiting sources. Footage is never looped, frozen, slowed, duplicated, or
padded to manufacture compliance.

### 22.5 Orchestration: `src/auto_pipeline.py`

`prepare` performs discovery, metadata inspection, camera grouping, sync
assistance, project/EDL generation where safe, serialized-artifact validation, and
an actionable summary, then stops before rendering.

The orchestrator passes the selected evidence-backed group to the existing sync
assistant. It prints the number of analyzed pairs, excluded derived outputs,
grouping state, score, and selected paths. Generated artifacts carrying the
automation provenance can be refreshed on a repeat run; user-authored manual
configuration is never replaced implicitly.

`auto` runs the same preparation and may invoke the existing atomic draft renderer.
Automatically detected but unverified synchronization is included in the project
and draft filename and in evidence. `auto` never imports or invokes approval.
Smoke mode requires `--allow-smoke`, includes `smoke` in artifact names, stays
under `output/draft`, and is rejected by final approval policy.

The typed outcome states are:

- `READY_FOR_DRAFT`
- `READY_FOR_SMOKE_ONLY`
- `NEEDS_CAMERA_SELECTION`
- `NEEDS_SYNC_CONFIRMATION`
- `INSUFFICIENT_COMMON_DURATION`
- `INVALID_INPUT`
- `DRAFT_RENDERED`
- `DRAFT_RENDERED_WITH_UNVERIFIED_SYNC`

These states distinguish successful preparation from submission readiness.
Rendering a smoke or unverified-sync draft is technical success only; complete
human visual, audio, privacy, licensing, and clap verification is still mandatory.
