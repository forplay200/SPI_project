# DESIGN.md

## AI-Assisted Multi-Camera Kindergarten Graduation Video Editing Pipeline

**Document type:** UI/UX and application design specification  
**Design status:** Initial implementation-ready design  
**UI style:** Guided Automation Workflow Wizard  
**Frontend:** React, TypeScript, Vite, Tailwind CSS, shadcn/ui  
**Backend:** FastAPI wrapping the existing Python automation pipeline  
**Processing model:** Local-first, semi-automated, human-controlled  

---

## 1. Purpose

This document defines the user experience, visual design, frontend structure, backend API boundary, application states, and acceptance criteria for the graphical user interface of the AI-Assisted Multi-Camera Kindergarten Graduation Video Editing Pipeline.

The interface must make the system's automation visible and understandable. A non-technical user should be able to select a local footage folder, allow the system to analyse all eligible videos, review synchronisation suggestions, inspect an automatically generated Editing Decision List (EDL), render a draft, and complete human review without manually editing JSON files or using command-line commands.

The UI does not replace the existing Python pipeline. The React frontend and FastAPI backend must reuse the existing discovery, grouping, synchronisation, EDL generation, validation, rendering, evidence, review, and approval modules.

---

## 2. Product Experience Goal

The target experience is:

```text
Select local footage
        ↓
Automatically discover and inspect all videos
        ↓
Automatically group related camera recordings
        ↓
Suggest synchronisation cues and offsets
        ↓
Human verifies the synchronisation when required
        ↓
Automatically generate and validate an EDL
        ↓
Automatically render and validate a Draft MP4
        ↓
Human reviews the complete Draft
        ↓
Eligible Draft is approved and promoted to Final
```

The user should not normally need to create or edit:

- `project.json`;
- `sync.json`;
- `editing_decisions.json`;
- FFmpeg commands;
- MoviePy code;
- render evidence JSON;
- approval records.

These files remain available as transparent evidence and advanced configuration outputs.

---

## 3. Design Direction

### 3.1 Selected Style

The selected style is **Guided Automation Workflow Wizard**.

The interface presents one focused stage at a time and uses a persistent six-step progress indicator:

1. Footage
2. Analysis
3. Synchronisation
4. Editing Plan
5. Draft Review
6. Approval

This style is selected because it:

- highlights automatic work performed by the system;
- reduces technical complexity for teachers and non-technical reviewers;
- makes human checkpoints explicit;
- avoids resembling a full professional timeline editor;
- supports clear classroom demonstration;
- provides visible evidence of privacy-aware, local processing;
- preserves explainability for every important automated decision.

### 3.2 Design Keywords

- Professional
- Guided
- Calm
- Trustworthy
- Privacy-aware
- Explainable
- Local-first
- Human-controlled
- Accessible
- Media-focused
- Minimal

### 3.3 Styles to Avoid

- Neon or cyberpunk visual styling
- Excessive gradients
- Childish cartoon decoration
- Face-analysis dashboards
- Chatbot-centred interaction
- Complex Premiere-style multi-track editing
- Excessive animation
- Hidden automatic decisions
- Misleading AI or machine-learning claims

The product involves kindergarten graduation footage, but the operator is an adult teacher, editor, student, or reviewer. The application shell should therefore remain professional rather than child-themed.

---

## 4. Core Design Principles

### 4.1 Automation Must Be Visible

The UI must show the automatic operations being performed, such as:

- discovering videos;
- probing media metadata;
- excluding likely derived outputs;
- analysing camera pairs;
- grouping related recordings;
- choosing a master camera;
- detecting audio cue candidates;
- calculating offsets;
- generating camera switches;
- validating the EDL;
- rendering the video;
- validating the output;
- generating evidence.

The UI must not display only an indefinite spinner with no explanation.

### 4.2 Human Control Must Be Explicit

The following actions remain human-controlled:

- confirming whether an audio cue is a valid synchronisation point;
- correcting automatically generated editing decisions when necessary;
- reviewing the entire Draft visually and audibly;
- completing the review checklist;
- approving an eligible Draft as Final.

### 4.3 Explain Every Automated Decision

Every selected camera group, synchronisation suggestion, EDL segment, validation warning, and approval restriction must have a human-readable explanation.

### 4.4 Preserve Honest Capability Claims

The UI must describe camera selection and EDL generation as **deterministic rule-based automation** unless a separate, verified machine-learning component is added in the future.

The UI must not claim:

- autonomous editing;
- verified clap detection when only a transient was detected;
- submission readiness for smoke outputs;
- approval for an unreviewed or modified Draft.

### 4.5 Local Processing Must Be Reassuring and Visible

A persistent indicator must communicate:

```text
Local Processing
Footage is not uploaded
```

The application must not contain cloud upload controls or hidden telemetry for the footage-processing workflow.

### 4.6 Safe Failure Is Better Than False Success

If the system cannot reliably select a camera group, synchronise footage, reach the requested duration, or validate the output, the UI must show a clear blocked or needs-action state. The application must not silently fabricate timestamps, repeat footage, or bypass validation.

---

## 5. Target Users

### 5.1 Primary User: Teacher or Editor

Needs:

- a simple guided workflow;
- minimal technical configuration;
- understandable warnings;
- an easy way to review the generated video;
- confidence that footage remains local.

### 5.2 Project Team Member

Needs:

- access to generated configuration, EDL, evidence, and logs;
- visible automation results for demonstration;
- the ability to correct generated decisions;
- clear error information.

### 5.3 Human Reviewer

Needs:

- full Draft playback;
- synchronisation and quality information;
- a complete checklist;
- clear approval eligibility;
- protection against approving a changed file.

### 5.4 Lecturer or Evaluator

Needs:

- evidence that all source videos were analysed;
- a visible EDL-to-code bridge;
- camera grouping and switching explanations;
- privacy and human-review controls;
- honest distinction between automation and AI.

---

## 6. Information Architecture

```text
Application
├── Home / Project Setup
├── Workflow
│   ├── 1. Footage
│   ├── 2. Camera Analysis
│   ├── 3. Synchronisation
│   ├── 4. Editing Plan
│   ├── 5. Draft Review
│   └── 6. Approval
├── Evidence
│   ├── Media Inventory
│   ├── Camera Grouping Report
│   ├── Synchronisation Report
│   ├── Generated EDL
│   ├── Render Report
│   └── Approval Record
└── Settings
    ├── FFmpeg / FFprobe Status
    ├── Output Defaults
    ├── Local Storage Paths
    └── Licence Information
```

The primary workflow should use the six-stage wizard. Evidence and Settings may be available from secondary navigation without interrupting the active workflow.

---

## 7. Global Application Layout

### 7.1 Desktop Layout

```text
┌─────────────────────────────────────────────────────────────┐
│ Product Name       Local Processing ●        Project Menu   │
├─────────────────────────────────────────────────────────────┤
│ 1 Footage  2 Analysis  3 Sync  4 Plan  5 Review  6 Approve │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    Active Step Content                      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Status / warnings                    Back     Continue       │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Header

The header contains:

- product name;
- current project title;
- local-processing status;
- backend connection status;
- evidence shortcut;
- settings shortcut;
- project menu.

### 7.3 Workflow Stepper

The stepper remains visible on all workflow screens.

Step states:

- `Not Started`
- `In Progress`
- `Completed`
- `Needs Review`
- `Blocked`
- `Failed`

Completed steps may be revisited. Returning to an earlier step must invalidate later outputs if the relevant inputs have changed.

### 7.4 Action Footer

The footer contains context-sensitive actions:

- Back
- Save
- Retry
- Continue
- Generate Plan
- Render Draft
- Request Changes
- Approve Final

Destructive or state-invalidating actions require a confirmation dialog explaining the consequence.

---

## 8. Screen Specifications

## 8.1 Screen 1: Project Setup and Footage

### Purpose

Allow a user to create a project and select a local input folder with minimal configuration.

### Required Fields

- Project title
- Input folder
- Target duration
- Output resolution
- Output frame rate
- Mode

### Modes

- **Normal Draft:** requires the configured compliant duration and approval conditions.
- **Smoke Test:** allows a short technical Draft and clearly marks the result as non-compliant and approval-ineligible.

### Defaults

- Resolution: 1280 × 720
- Frame rate: 30 fps
- Renderer: MoviePy
- FFmpeg fallback: enabled
- Target duration: 90 seconds
- Mode: Normal Draft

### Important UI Copy

```text
All footage is processed locally. No video is uploaded by this application.
```

```text
The system will inspect all eligible videos in the selected folder and attempt
to identify recordings of the same event automatically.
```

### Primary Action

```text
Analyse Footage
```

### Validation

- Folder must exist.
- Folder must be readable.
- At least two eligible video files must be available for automatic multi-camera editing.
- Target duration must be valid for the selected mode.
- The UI must warn about likely generated output files but should not delete them.

---

## 8.2 Screen 2: Automatic Camera Analysis

### Purpose

Demonstrate that the system analysed all input videos and selected a supported multi-camera group.

### Automation Progress

Display individual tasks:

```text
Discovering video files
Reading media metadata
Excluding generated outputs
Normalising recording timestamps
Preparing local audio analysis
Comparing camera pairs
Scoring candidate groups
Selecting master camera
```

### Summary Metrics

- Videos discovered
- Eligible source candidates
- Derived outputs excluded
- Camera pairs analysed
- Cameras selected
- Best group score
- Group confidence state
- Common Synchronized Overlap
- Total Event Coverage
- Maximum Renderable Duration

Common overlap is the intersection of every selected camera timeline and is
labelled as synchronization information only. Total event coverage is the union
of synchronized timelines. Maximum renderable duration is calculated by valid
per-segment camera assignment and is the only one of these metrics used as the
automatic generation limit.

### Selected Camera Cards

Each selected camera card shows:

- stable camera ID;
- filename;
- source-relative path;
- duration;
- resolution;
- frame rate;
- codec;
- audio availability;
- selected/master status;
- analysis warnings.

### Excluded Files Section

Display a collapsible list with the reason for exclusion, such as:

- likely final output;
- likely draft output;
- unsupported format;
- unreadable media;
- zero duration;
- likely derived duplicate;
- insufficient supporting evidence.

### Pair Analysis Drawer

Allow the user to inspect pair-level evidence:

- pair filenames;
- score;
- filename-time signal;
- media creation-time signal;
- audio similarity;
- estimated offset;
- shared transient strength;
- offset stability;
- derived-output penalty;
- acceptance or rejection reason.

### Outcome States

- `CAMERA_GROUP_CONFIRMED`
- `CAMERA_GROUP_SUGGESTED`
- `CAMERA_GROUP_LOW_CONFIDENCE`
- `NO_RELIABLE_CAMERA_GROUP`
- `DERIVED_OUTPUTS_ONLY`

### User Actions

- Accept Suggested Group
- Select Different Cameras
- Reanalyse
- Continue to Synchronisation

Explicit user selection may replace automatic grouping, but it must not bypass media, sync, duration, EDL, privacy, or approval validation.

---

## 8.3 Screen 3: Synchronisation Verification

### Purpose

Present automatically suggested audio cues and let a human verify or adjust them without editing JSON.

### Master Camera Panel

Display:

- master camera ID;
- filename;
- suggested cue timestamp;
- cue type;
- confidence;
- verification status.

### Camera Synchronisation Cards

For each camera, display:

- suggested cue timestamp;
- estimated offset;
- confidence score;
- cue type;
- supporting metric;
- human verification requirement;
- warning text.

### Cue Types

- `clap_candidate`
- `shared_audio_transient`
- `low_confidence_candidate`
- `no_reliable_candidate`
- `manually_verified_clap`

### Cue Preview

Provide controls to play a local preview window around the candidate cue:

- Play from 2 seconds before cue
- Pause
- Replay
- Show waveform or energy preview if available

The preview must not upload or expose footage externally.

### User Actions

- Confirm Cue
- Adjust Timestamp
- Reject Candidate
- Analyse Again
- Select Another Candidate

### Important Copy

```text
A shared audio transient is a synchronisation suggestion. It is not a verified
clap until a human reviewer confirms the cue.
```

### Synchronisation States

- `NOT_RUN`
- `CANDIDATES_FOUND`
- `NEEDS_SYNC_CONFIRMATION`
- `LOW_CONFIDENCE`
- `NO_RELIABLE_CUE`
- `SYNC_CONFIRMED`

A smoke Draft may be rendered with unverified sync only when the user explicitly selects Smoke Test mode. Such a Draft must remain approval-ineligible.

The Synchronisation screen may display Common Synchronized Overlap as a sync
quality diagnostic. It must not describe that value as the available edit or
maximum project duration.

---

## 8.4 Screen 4: Generated Editing Plan

### Purpose

Visualise the automatically generated EDL and allow limited, explainable corrections.

### Automation Summary

Display:

- target duration;
- maximum renderable duration;
- common overlap and total event coverage as secondary explanatory metrics;
- generated segment count;
- cameras used;
- camera switch count;
- transition count;
- overlay count;
- validator status.

### Simplified Timeline

Display a single-row sequence of segments rather than a full professional multi-track editor.

```text
0s          5s          10s         15s         20s
[Camera 02] [Camera 01] [Camera 03] [Camera 02]
 Fade In       Cut          Cut       Fade Out
```

Camera colours:

- Camera 01: Blue
- Camera 02: Purple
- Camera 03: Teal
- Camera 04: Orange

Colours must remain accessible and must not be the only way to identify cameras. Camera labels and patterns or icons should also be present.

### Segment Detail Panel

When a segment is selected, display:

- segment ID;
- start time;
- end time;
- duration;
- selected camera;
- action;
- overlay;
- decision reason;
- generator provenance;
- validation state;
- human-review requirement.

### Allowed Edits

- choose another valid camera;
- adjust start and end times;
- edit decision reason;
- choose a supported transition;
- edit lower-third text;
- remove or add an allowed overlay.

### Excluded Editing Features

- unlimited multi-track editing;
- colour grading;
- keyframe animation;
- advanced audio mixing;
- free-form visual effects;
- overlapping crossfade mathematics in the minimum UI;
- face-based selection.

### Validation Behaviour

Any edit triggers revalidation. The interface must visibly reject:

- overlapping segments;
- gaps where continuity is required;
- unknown cameras;
- unsupported actions;
- source-boundary violations;
- fewer than two cameras;
- fewer than three switches;
- invalid duration;
- missing reasons;
- missing required presentation elements.

When target duration exceeds maximum renderable duration, the warning must refer
to renderable coverage, not common overlap.

### Primary Action

```text
Render Draft
```

---

## 8.5 Screen 5: Render and Draft Review

### Purpose

Show rendering progress, play the resulting Draft, and collect complete human review evidence.

### Render Progress

Display stages such as:

```text
Preparing source clips
Applying synchronisation offsets
Switching camera angles
Adding opening title
Adding lower-third
Adding closing credits
Encoding MP4
Validating output
Generating evidence
```

### Render Job Information

- current stage;
- progress percentage;
- elapsed time;
- selected renderer;
- fallback state;
- current warning;
- cancel status, if safe cancellation is supported.

### Draft Player

Use a dark media area within the light interface.

Player controls:

- play/pause;
- seek;
- volume;
- fullscreen;
- current time and duration;
- optional segment marker overlay;
- optional jump to previous/next camera switch.

### Draft Technical Summary

- common synchronized overlap;
- total event coverage;
- maximum renderable duration;
- duration;
- number of cameras used;
- camera switches;
- renderer;
- fallback used;
- video codec;
- audio codec;
- resolution;
- frame rate;
- output checksum;
- sync status;
- compliance status.

### Review Checklist

The reviewer must confirm:

- Video opens successfully.
- Full Draft was watched.
- Camera switches are visually continuous.
- Audio remains understandable.
- Synchronisation is acceptable.
- Opening title is readable.
- Lower-third or subtitle is readable.
- Closing credits are readable.
- Required transition is visible.
- Important moments are retained.
- No unintended personal information appears.
- Footage use is authorised.
- Music, fonts, and other assets have acceptable licences.

### Review Actions

- Request Changes
- Save Review Progress
- Complete Review
- View Evidence

Request Changes must return the user to the relevant step and explain which generated outputs will become invalid.

---

## 8.6 Screen 6: Final Approval

### Purpose

Promote only an eligible, unchanged, completely reviewed Draft into the Final output area.

### Approval Requirements

The Approve Final button is enabled only when:

- the Draft is not a smoke output;
- duration is within the configured accepted range;
- synchronisation is confirmed;
- output validation passed;
- the review checklist is complete;
- reviewer name is provided;
- approval comments are recorded where required;
- the Draft checksum matches the reviewed checksum;
- the Draft is located in the authorised Draft directory;
- no blocking privacy or licensing issue remains.

### Disabled Approval Explanation

When approval is unavailable, display all reasons, for example:

```text
Final Approval Unavailable

• This output is a Smoke Draft.
• Duration is below 60 seconds.
• Synchronisation has not been manually verified.
```

### Approval Action

```text
Approve Final
```

Approval must not modify or rerender the video. It must promote the exact reviewed binary whose SHA-256 matches the approval record.

### Approval Result

Display:

- Final path;
- approval timestamp;
- reviewer;
- SHA-256;
- review record path;
- evidence links.

---

## 8.7 Evidence Screen

### Purpose

Make the automated pipeline transparent and support academic evaluation.

### Evidence Categories

- Input media inventory
- Excluded-files report
- Camera grouping analysis
- Pairwise scores
- Synchronisation suggestions
- Confirmed offsets
- Generated project configuration
- Generated EDL
- EDL validation report
- Render report
- Output probe report
- SHA-256
- Review checklist
- Approval record
- Software and asset licences

### Actions

- View JSON
- Download JSON
- Copy file path
- Open containing folder
- Export evidence summary

Sensitive media should not be embedded in evidence by default. Frame screenshots should be optional and privacy-reviewed.

Generated project evidence stores `common_overlap_duration`,
`total_event_coverage`, and `maximum_renderable_duration`. These values remain
available on the Evidence screen alongside the EDL and render reports.

---

## 9. Main User Flows

## 9.1 Automatic Normal Workflow

```text
Create project
→ Choose input folder
→ Set title and target duration
→ Analyse footage
→ Review selected camera group
→ Verify sync cues
→ Generate EDL
→ Review or adjust EDL
→ Render Draft
→ Watch complete Draft
→ Complete checklist
→ Approve Final
```

## 9.2 Automatic Smoke Workflow

```text
Create project in Smoke Test mode
→ Analyse all footage
→ Select supported camera group
→ Generate sync suggestions
→ Generate short EDL
→ Render clearly labelled Smoke Draft
→ Review technical result
→ Approval remains disabled
```

## 9.3 Low-Confidence Camera Group

```text
Analyse footage
→ No reliable group found
→ Show ranked candidate groups and reasons
→ User selects at least two camera files
→ System validates explicit group
→ Continue to sync analysis
```

## 9.4 Low-Confidence Synchronisation

```text
Detect cue candidates
→ Show low-confidence warning
→ User previews candidate regions
→ User confirms or adjusts timestamps
→ System recalculates offsets
→ Revalidate common timeline
→ Continue
```

## 9.5 Request Changes After Review

```text
Reviewer finds an issue
→ Select Request Changes
→ Record issue and affected segment
→ Return to Sync or Editing Plan
→ Change invalidates old Draft and approval eligibility
→ Rerender
→ Review new checksum
```

---

## 10. Visual Design System

## 10.1 Colour Tokens

```text
Background             #F7F9FC
Surface                #FFFFFF
Surface Subtle         #F1F5F9
Video Surface          #0E1117
Primary                #2563EB
Primary Hover          #1D4ED8
Primary Soft           #DBEAFE
Success                #16866F
Success Soft           #DDF7EF
Warning                #D97706
Warning Soft           #FFF2D8
Danger                 #DC3944
Danger Soft            #FEE2E2
Main Text              #172033
Secondary Text         #667085
Muted Text             #98A2B3
Border                 #DDE3EC
Focus Ring             #60A5FA
```

### Status Colour Rules

- Blue: current or ready action
- Green: completed or confirmed
- Amber: human confirmation required
- Red: blocked, failed, or unsafe
- Grey: unavailable or not started
- Purple: automatic processing activity

Colour must never be the only status indicator. Use icons and text labels.

## 10.2 Typography

```text
Font family: "Segoe UI", Inter, Arial, sans-serif
Page title: 28–32 px, semibold
Section title: 20–24 px, semibold
Card title: 16–18 px, semibold
Body: 14–16 px, regular
Metadata: 12–14 px, regular
Button: 14–16 px, medium
```

## 10.3 Spacing

Use an 8-pixel spacing system:

```text
4, 8, 12, 16, 24, 32, 40, 48
```

## 10.4 Shape

- Cards: 12–16 px corner radius
- Buttons: 8–10 px corner radius
- Inputs: 8 px corner radius
- Status badges: pill shape
- Borders: 1 px
- Shadows: soft and minimal

## 10.5 Icons

Use Lucide icons consistently.

Suggested mappings:

- FolderOpen: footage
- ScanSearch: analysis
- Camera: camera source
- AudioWaveform: synchronisation
- ListVideo: EDL
- WandSparkles: deterministic automation
- Film: render
- ClipboardCheck: review
- ShieldCheck: approval/privacy
- TriangleAlert: warning
- CircleCheck: completed
- Lock: local/private processing

Avoid robot-head icons as the main identity because the system is not primarily a chatbot or autonomous AI.

---

## 11. Component Library

### Core Components

- AppHeader
- WorkflowStepper
- StepStatusBadge
- LocalProcessingBadge
- ProjectSummaryCard
- AutomationProgressList
- JobProgressPanel
- CameraCard
- CameraGroupScoreCard
- PairAnalysisDrawer
- ExcludedFileList
- SyncCueCard
- CuePreviewPlayer
- ConfidenceMeter
- EditingTimeline
- EDLSegmentCard
- SegmentEditDialog
- ValidationIssueList
- DraftVideoPlayer
- TechnicalSummaryCard
- ReviewChecklist
- ApprovalEligibilityPanel
- EvidenceFileList
- EmptyState
- ErrorState
- ConfirmationDialog
- ToastNotification

### Component Behaviour

- Use skeleton placeholders during short data loads.
- Use detailed progress panels during long-running analysis or rendering.
- Persist step state after browser refresh.
- Preserve unsaved form changes or warn before leaving.
- Display backend validation errors beside the affected field and in a summary.

---

## 12. Frontend Architecture

## 12.1 Technology

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- Lucide React
- React Router
- TanStack Query
- React Hook Form
- Zod for client-side input validation

## 12.2 Proposed Structure

```text
frontend/
├── src/
│   ├── app/
│   │   ├── router.tsx
│   │   ├── queryClient.ts
│   │   └── providers.tsx
│   ├── components/
│   │   ├── common/
│   │   ├── workflow/
│   │   ├── cameras/
│   │   ├── sync/
│   │   ├── edl/
│   │   ├── review/
│   │   └── evidence/
│   ├── pages/
│   │   ├── ProjectSetupPage.tsx
│   │   ├── CameraAnalysisPage.tsx
│   │   ├── SynchronisationPage.tsx
│   │   ├── EditingPlanPage.tsx
│   │   ├── DraftReviewPage.tsx
│   │   ├── ApprovalPage.tsx
│   │   ├── EvidencePage.tsx
│   │   └── SettingsPage.tsx
│   ├── services/
│   │   ├── apiClient.ts
│   │   ├── projectsApi.ts
│   │   ├── jobsApi.ts
│   │   └── evidenceApi.ts
│   ├── hooks/
│   ├── types/
│   ├── utils/
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── vite.config.ts
```

## 12.3 State Strategy

- Server state: TanStack Query
- Forms: React Hook Form
- URL state: React Router
- Temporary component state: React state
- Long-running job state: backend job endpoint with polling

Avoid placing the complete application state in one global store unless implementation evidence shows it is necessary.

---

## 13. Backend Architecture

## 13.1 Technology

- FastAPI
- Pydantic
- Existing Python pipeline modules
- Background task execution
- Status polling for prototype implementation

A production message queue is outside the minimum scope. The prototype may use a controlled in-process job manager, provided concurrent jobs and process restarts are documented honestly.

## 13.2 Backend Responsibilities

The FastAPI backend must:

- validate API requests;
- create project records;
- invoke existing Python business functions directly;
- start and monitor long-running jobs;
- return progress and structured results;
- serve approved local media files safely;
- expose generated evidence;
- record sync confirmations;
- save EDL corrections;
- create review records;
- invoke checksum-bound approval.

The backend must not shell out to the CLI command `python -m src.main` as its primary integration method. CLI and API should call the same reusable service functions.

## 13.3 Proposed Backend Structure

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── projects.py
│   │   ├── analysis.py
│   │   ├── sync.py
│   │   ├── edl.py
│   │   ├── render.py
│   │   ├── review.py
│   │   ├── approval.py
│   │   └── evidence.py
│   ├── schemas/
│   ├── services/
│   │   ├── project_service.py
│   │   ├── automation_service.py
│   │   ├── job_service.py
│   │   └── media_service.py
│   └── security/
│       └── path_policy.py
└── tests/
```

The existing `src/` directory remains the domain and pipeline layer.

---

## 14. API Design

### Project

```text
POST   /api/projects
GET    /api/projects/{project_id}
PUT    /api/projects/{project_id}
DELETE /api/projects/{project_id}
```

### Footage and Analysis

```text
POST   /api/projects/{project_id}/analysis
GET    /api/projects/{project_id}/analysis
GET    /api/projects/{project_id}/cameras
PUT    /api/projects/{project_id}/camera-group
```

### Synchronisation

```text
POST   /api/projects/{project_id}/sync/detect
GET    /api/projects/{project_id}/sync
POST   /api/projects/{project_id}/sync/confirm
POST   /api/projects/{project_id}/sync/reject
```

### EDL

```text
POST   /api/projects/{project_id}/edl/generate
GET    /api/projects/{project_id}/edl
PUT    /api/projects/{project_id}/edl
POST   /api/projects/{project_id}/edl/validate
```

### Render

```text
POST   /api/projects/{project_id}/render
GET    /api/projects/{project_id}/draft
GET    /api/projects/{project_id}/draft/media
```

### Jobs

```text
GET    /api/jobs/{job_id}
POST   /api/jobs/{job_id}/cancel
```

### Review and Approval

```text
POST   /api/projects/{project_id}/review
GET    /api/projects/{project_id}/review
POST   /api/projects/{project_id}/approve
GET    /api/projects/{project_id}/approval
```

### Evidence

```text
GET    /api/projects/{project_id}/evidence
GET    /api/projects/{project_id}/evidence/{evidence_id}
GET    /api/projects/{project_id}/files/{file_id}
```

---

## 15. Long-Running Job Design

### Job States

- `QUEUED`
- `DISCOVERING`
- `PROBING_MEDIA`
- `GROUPING_CAMERAS`
- `ANALYSING_AUDIO`
- `GENERATING_EDL`
- `VALIDATING`
- `RENDERING`
- `VALIDATING_OUTPUT`
- `GENERATING_EVIDENCE`
- `COMPLETED`
- `FAILED`
- `CANCELLED`

### Example Job Response

```json
{
  "job_id": "job-20260729-001",
  "status": "ANALYSING_AUDIO",
  "progress": 42,
  "message": "Comparing audio evidence for 21 camera pairs",
  "current_step": 2,
  "warning": null,
  "result": null
}
```

The frontend may poll every one to two seconds. Polling stops when the job reaches a terminal state.

The progress value must reflect meaningful stages. It must not randomly increase to simulate progress.

---

## 16. Application Outcome States

The UI must support these high-level outcomes:

- `READY_FOR_DRAFT`
- `READY_FOR_SMOKE_ONLY`
- `NEEDS_CAMERA_SELECTION`
- `NEEDS_SYNC_CONFIRMATION`
- `INSUFFICIENT_RENDERABLE_DURATION`
- `INVALID_INPUT`
- `DRAFT_RENDERED`
- `DRAFT_RENDERED_WITH_UNVERIFIED_SYNC`
- `REVIEW_REQUIRED`
- `CHANGES_REQUIRED`
- `READY_FOR_APPROVAL`
- `APPROVED`

Each state must have:

- label;
- icon;
- severity;
- explanation;
- next recommended action;
- permitted actions;
- prohibited actions.

---

## 17. Error and Empty States

### Error Message Pattern

Every error should explain:

1. What happened
2. Why it matters
3. What the user can do next

Example:

```text
No reliable camera group was found.

The system analysed 21 camera pairs but did not find enough evidence that two
files recorded the same event.

Review the ranked candidates or select at least two related camera files
manually.
```

### Important Error Cases

- No video files found
- Fewer than two eligible camera sources
- Unsupported format
- FFmpeg unavailable
- FFprobe unavailable
- No audio stream
- No reliable camera group
- No reliable sync cue
- Insufficient renderable duration
- EDL validation failure
- Segment exceeds source boundary
- Render failure
- Fallback activated
- Output validation failure
- Draft changed after review
- Approval unavailable

Raw stack traces must not be shown as the primary UI message. Detailed technical logs may be available under Evidence or Advanced Details.

---

## 18. Privacy and Security Design

### 18.1 Local-Only Behaviour

- The browser UI communicates only with the local FastAPI service by default.
- The interface must not offer cloud upload.
- Source video paths must remain local.
- Generated previews must be served only through controlled local endpoints.

### 18.2 Path Safety

The backend must:

- resolve and validate all paths;
- reject traversal outside authorised project directories;
- avoid accepting arbitrary absolute paths from API clients where possible;
- restrict media serving to registered project files;
- never overwrite source videos;
- never write renders directly into the Final directory.

### 18.3 Sensitive Information

- Do not display inferred identities.
- Do not analyse faces or emotions.
- Do not place personal names from footage into logs.
- Do not create screenshots by default.
- Avoid exposing full user-home paths in presentation mode.

### 18.4 Approval Integrity

- Approval is tied to SHA-256.
- Approval does not alter the video.
- Changed Drafts require a new review.
- Smoke and unverified-sync outputs remain approval-ineligible.

---

## 19. Accessibility

The UI should target WCAG 2.1 AA principles where practical.

Requirements:

- keyboard-accessible controls;
- visible focus indicators;
- semantic headings;
- form labels;
- accessible error descriptions;
- captions or text alternatives for instructional media where available;
- sufficient colour contrast;
- status indicators that include text and icon, not colour alone;
- no critical interaction requiring drag-and-drop only;
- timeline segments accessible by keyboard;
- reduced-motion support;
- readable layout at 200% zoom.

---

## 20. Responsive Behaviour

### Desktop: 1280 px and above

- Full workflow stepper labels
- Side-by-side media and details
- Timeline visible horizontally
- Review checklist beside video player

### Tablet: 768–1279 px

- Condensed workflow stepper
- Stacked camera cards
- Details panel below timeline
- Review checklist below player

### Small Screens: Below 768 px

- Primarily for status checking, simple confirmation, and evidence viewing
- Stepper becomes a compact progress header
- Timeline becomes horizontally scrollable
- Complex segment editing should show a recommendation to use a larger screen

A mobile application is out of scope. Responsive web behaviour does not mean full mobile editing support.

---

## 21. Content and Language Guidelines

### Tone

- Clear
- Calm
- Specific
- Non-technical where possible
- Honest about limitations

### Preferred Terms

Use:

- Automatic analysis
- Rule-based editing plan
- Synchronisation suggestion
- Human verification required
- Local processing
- Draft
- Final approval

Avoid:

- AI knows
- Perfect sync
- Fully autonomous
- Guaranteed best angle
- Child recognition
- Emotion detection

### Closing Credits

The visible closing credit should use professional, configurable text such as:

```text
Edited by the Project Team
BTIS3053 Social & Professional Issues
```

Human-review requirements should remain in the UI, evidence, filenames, and approval rules rather than appearing as awkward default closing-credit text.

---

## 22. UI Testing Strategy

### Unit Tests

- workflow state rendering;
- stepper transitions;
- form validation;
- status badges;
- camera-card states;
- confidence display;
- EDL segment validation messages;
- approval eligibility logic;
- error and empty states.

### Component Tests

- project setup form;
- automation progress list;
- camera group selection;
- cue confirmation;
- timeline interaction;
- review checklist;
- approval panel.

### API Integration Tests

- project creation;
- analysis job polling;
- camera-group result display;
- sync confirmation;
- EDL generation and update;
- render job progress;
- media playback endpoint;
- review submission;
- approval rejection and success.

### End-to-End Tests

1. Automatic smoke workflow with short local synthetic footage.
2. Compliant 60–180 second synthetic workflow.
3. Low-confidence camera grouping requiring selection.
4. Low-confidence sync requiring confirmation.
5. Request Changes and rerender flow.
6. Smoke approval rejection.
7. Unverified-sync approval rejection.
8. Changed-checksum approval rejection.
9. Eligible reviewed Draft approval.

Use synthetic footage in automated tests. Do not commit sensitive or large media files.

---

## 23. Implementation Phases

### Phase 1: Backend API Foundation

- Add FastAPI application.
- Add health and preflight endpoints.
- Add project models and storage.
- Expose existing discovery and grouping services.
- Add background job status model.

### Phase 2: Frontend Foundation

- Create React TypeScript project.
- Configure Tailwind and shadcn/ui.
- Implement application shell and workflow stepper.
- Implement project setup screen.
- Connect backend health status.

### Phase 3: Camera Analysis

- Add analysis job endpoint.
- Add polling.
- Build progress display.
- Build camera cards, excluded files, and pair analysis.

### Phase 4: Synchronisation

- Expose cue detection and confirmation.
- Implement cue preview endpoint.
- Build synchronisation cards and confirmation controls.

### Phase 5: Editing Plan

- Expose EDL generation, retrieval, update, and validation.
- Build simplified timeline.
- Build segment detail and edit controls.

### Phase 6: Render and Review

- Expose render jobs and media playback.
- Build render progress and Draft player.
- Build checklist and review submission.

### Phase 7: Approval and Evidence

- Expose approval eligibility and approval operation.
- Build disabled-state explanations.
- Build evidence browser and download controls.

### Phase 8: Quality and Documentation

- Accessibility review.
- Responsive review.
- Full automated testing.
- Privacy and path-safety review.
- README update.
- Architecture and handoff update.

---

## 24. Design Acceptance Criteria

The UI design is successfully implemented when:

- [ ] A user can create a project without editing JSON.
- [ ] A user can select a local footage folder.
- [ ] The UI shows that all eligible videos are being analysed.
- [ ] Derived outputs and excluded files are visible with reasons.
- [ ] Camera grouping score and confidence are visible.
- [ ] Selected and master cameras are visible.
- [ ] Synchronisation candidates and offsets are visible.
- [ ] A user can preview, confirm, reject, or adjust a sync cue.
- [ ] The UI never labels an unverified transient as a verified clap.
- [ ] A valid EDL can be generated automatically.
- [ ] The generated EDL is shown as a simplified timeline.
- [ ] Every segment has a human-readable reason.
- [ ] Limited EDL corrections can be made without editing JSON.
- [ ] Draft rendering shows meaningful progress.
- [ ] The rendered Draft can be played locally in the UI.
- [ ] The review checklist can be completed and saved.
- [ ] Smoke outputs clearly show non-compliant status.
- [ ] Unverified-sync outputs clearly show restricted status.
- [ ] Approval eligibility reasons are visible.
- [ ] Approval promotes the unchanged reviewed SHA-256.
- [ ] Evidence can be viewed from the UI.
- [ ] The existing CLI remains functional.
- [ ] The backend reuses existing Python business modules.
- [ ] Footage remains local.
- [ ] No face, identity, or emotion analysis is introduced.
- [ ] Automated UI, API, and end-to-end tests pass.

---

## 25. Definition of Done

The UI feature is complete when:

1. The six-stage guided workflow is usable from project creation to approval.
2. The interface visibly demonstrates automation at every relevant stage.
3. React communicates with FastAPI through typed API contracts.
4. FastAPI reuses the existing Python pipeline rather than duplicating it.
5. Long-running analysis and render operations provide meaningful progress.
6. Human sync verification, Draft review, and Final approval remain explicit.
7. Smoke and unverified outputs cannot be falsely approved.
8. Evidence and reasons remain accessible.
9. Local-only and privacy boundaries are preserved.
10. The existing command-line workflow and tests continue to pass.
11. UI, backend, architecture, README, and handoff documentation are consistent.

---

## 26. Final Design Decision Summary

```text
UI style:
Guided Automation Workflow Wizard

Theme:
Light professional interface with a dark video preview area

Primary navigation:
Six-stage horizontal workflow stepper

Frontend:
React + TypeScript + Vite + Tailwind CSS + shadcn/ui

Backend:
FastAPI wrapping the existing Python pipeline

Long-running operations:
Background execution with progress polling

Automation:
Video discovery, camera grouping, sync suggestions, EDL generation,
validation, rendering, and evidence generation

Human checkpoints:
Sync confirmation, complete Draft review, and Final approval

Capability description:
Deterministic rule-based automation with human oversight

Privacy model:
Local-only footage processing

Approval model:
Exact reviewed SHA-256 is promoted without rerendering
```
