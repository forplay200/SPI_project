# Product Requirements Document (PRD)

## AI-Assisted Multi-Camera Kindergarten Graduation Video Editing Pipeline

**Course:** BTIS3053 Social & Professional Issues  
**Official project title:** AI-Assisted Multi-Camera Kindergarten Graduation Video Editing Pipeline  
**PRD preparation and review duration:** 1 week  
**Prototype development duration:** Follow the assignment schedule and lecturer confirmation  
**Document status:** Revised Draft v2  
**Purpose of this document:** Define a clear, reviewable product scope before implementation begins

---

## 1. Important Timeline Clarification

The lecturer’s “reduce to 1 week” instruction applies to the **PRD discussion, critique, and revision process**, not necessarily to the entire prototype implementation.

The one-week PRD process should therefore be:

1. Discuss the project requirements with the first AI or coding agent.
2. Produce the first `PRD.md`.
3. Give the PRD to a different AI or agent for critical review.
4. Ask the second AI to grill the requirements, assumptions, scope, risks, and technical approach.
5. Return the critique to the original AI.
6. Revise the PRD until the team considers it clear and workable.
7. Only after PRD approval, prepare `architecture.md`, `design.md` if needed, and begin implementation.

The assignment document still describes the software work as a prototype project. Therefore, the implementation duration should not be silently changed inside the PRD unless the lecturer confirms a new implementation deadline.

---

## 2. Product Summary

Teachers may spend significant time reviewing, synchronising, cutting, and combining recordings from several cameras after a kindergarten graduation ceremony.

The project will design and prototype a semi-automated multi-camera video editing pipeline that:

- synchronises footage;
- selects useful segments;
- switches between camera angles;
- records decisions in an Editing Decision List (EDL);
- produces a 60–180 second final video;
- keeps humans responsible for review and approval;
- addresses children’s privacy, parental consent, Malaysia PDPA 2010, copyright, AI/software responsibility, and software licensing.

The system must not be described as fully autonomous.

---

## 3. Product Goal

Create a small, understandable, and responsible prototype that reduces repetitive video-editing work while keeping editing decisions visible and reviewable.

---

## 4. Problem Statement

Manual multi-camera editing requires teachers or editors to:

- compare several recordings;
- identify matching moments;
- synchronise footage;
- choose useful camera angles;
- cut and assemble clips;
- add basic presentation elements;
- review the final output.

This process is time-consuming and may introduce mistakes. A structured EDL-driven pipeline can reduce repetitive work while preserving human control.

---

## 5. Project Objectives

### 5.1 Primary Objectives

- Demonstrate multi-camera synchronisation.
- Use at least two camera angles.
- Include at least three camera switches.
- Generate and use a clear EDL.
- Produce a final MP4 between 60 and 180 seconds.
- Add an opening title, closing credits, one lower-third or subtitle, and one transition.
- Require human review before approval.
- Explain privacy, consent, PDPA, copyright, licensing, and professional responsibility.

### 5.2 PRD Objectives

During the one-week PRD phase, the team must:

- confirm the project scope;
- select one synchronisation method;
- select one rendering method;
- select one optional automation method;
- define testable requirements;
- define clear exclusions;
- identify ethical and legal constraints;
- obtain critique from a second AI or agent;
- revise and approve the PRD before implementation.

---

## 6. Stakeholders

| Stakeholder | Main Need |
|---|---|
| Kindergarten teacher or editor | Faster editing and easier review |
| Recorded children | Privacy, safety, and fair representation |
| Parents or guardians | Clear consent and controlled sharing |
| Project team | A feasible and understandable prototype |
| Lecturer or evaluator | Evidence of design, implementation, ethics, and professional responsibility |
| Human reviewer | Ability to inspect and correct editing decisions |

---

## 7. Scope

### 7.1 In Scope

- Simulated or lecturer-approved footage.
- At least two camera angles.
- At least three camera switches.
- Manual clap-based synchronisation.
- JSON, CSV, or spreadsheet EDL.
- Programmatic rendering.
- Rule-based or another lecturer-approved automation method.
- Opening title.
- Closing credits.
- One subtitle, label, or lower-third.
- One simple transition.
- Final output between 60 and 180 seconds.
- Human review.
- Local processing where possible.
- Basic validation and testing.
- Ethics, privacy, consent, PDPA, copyright, AI responsibility, and licensing discussion.

### 7.2 Out of Scope

- Face recognition.
- Emotion recognition.
- Child identification.
- Cloud-based processing of real children’s footage.
- Fully autonomous editing.
- Full professional timeline editor.
- Real-time editing.
- Mobile application.
- Production deployment.
- Advanced colour grading.
- Commercial-grade audio mastering.
- Any feature not approved in the final PRD.

---

## 8. Resolution of the “AI-Assisted” Naming Issue

The title **AI-Assisted Multi-Camera Kindergarten Graduation Video Editing Pipeline** is the official assignment title and should be retained.

However, the prototype must describe its actual technical method honestly.

The assignment allows an optional automation method such as:

- Auto-Editor;
- OpenCV;
- Whisper captions;
- rule-based camera switching.

Therefore:

- if the prototype uses only rule-based switching, it must be described as **semi-automated and rule-based**;
- the team must not claim that a machine-learning model performed the camera selection;
- the report may discuss AI responsibility and future AI improvements;
- any actual AI component must be clearly identified and evaluated;
- the word “AI-assisted” in the project title must not be used to exaggerate the implemented capability.

---

## 9. Proposed Technical Approach

### 9.1 Synchronisation Method

**Manual clap synchronisation**

Each camera video contains a visible or audible clap marker. The team records the clap timestamp for every camera and calculates the offset relative to one master camera.

Reason:

- easy to explain;
- easy to verify;
- suitable for a prototype;
- avoids unnecessary audio-fingerprinting complexity.

### 9.2 Rendering Method

**Primary option: MoviePy**

MoviePy reads the EDL, trims clips, applies synchronisation offsets, combines selected segments, adds text elements, applies a simple transition, and exports the MP4.

**Fallback option: direct FFmpeg commands**

FFmpeg should be retained as a fallback if MoviePy causes environment, text-rendering, or audio-sync problems.

### 9.3 Automation Method

**Rule-based camera switching expressed through the EDL**

Example rules:

- use the wide camera for group moments;
- use a closer camera for speeches;
- avoid blocked or unstable footage;
- avoid very rapid switching;
- keep each segment long enough to remain understandable.

This is deterministic automation, not machine learning.

---

## 10. User Workflow

1. Place camera videos in the input folder.
2. Record clap timestamps.
3. Calculate or enter camera offsets.
4. Review footage.
5. Create the EDL.
6. Validate the EDL.
7. Render the draft video.
8. Review the output.
9. Correct the EDL if necessary.
10. Render the final version.
11. Record human approval.

---

## 11. Functional Requirements

### FR-01: Load Input Videos

The system shall load at least two local video files.

**Acceptance criteria:**

- at least two supported video files open successfully;
- missing files produce a readable error;
- unsupported formats are rejected clearly.

### FR-02: Read Synchronisation Data

The system shall read clap timestamps or camera offsets from a configuration file.

**Acceptance criteria:**

- every camera has a valid timestamp or offset;
- one camera is identified as the master;
- invalid values are rejected;
- calculated offsets can be displayed for verification.

### FR-03: Load and Validate the EDL

The system shall load an EDL containing:

- start time;
- end time;
- selected camera;
- reason for selection;
- transition or editing action.

**Acceptance criteria:**

- malformed files are rejected;
- end time must be greater than start time;
- camera names must match configured sources;
- reasons cannot be empty;
- unsupported actions are rejected.

### FR-04: Extract Segments

The system shall trim the selected footage using synchronised timeline values.

**Acceptance criteria:**

- segment boundaries match the EDL;
- offsets are applied;
- no segment exceeds the available source duration.

### FR-05: Switch Cameras

The system shall combine footage from at least two cameras with at least three camera switches.

**Acceptance criteria:**

- at least four timeline segments are present;
- at least three changes occur between camera sources;
- segment order follows the EDL.

### FR-06: Opening Title

The system shall display an opening title before the main footage.

### FR-07: Closing Credits

The system shall display a closing credit screen after the main footage.

### FR-08: Subtitle, Label, or Lower-Third

The system shall display at least one readable subtitle, label, or lower-third.

### FR-09: Transition

The system shall include at least one simple transition because the assignment explicitly requires one.

To reduce implementation risk:

- the required transition should be limited to a simple fade-in, fade-out, or fade-to-black;
- crossfades are optional;
- the first version does not need overlapping transition mathematics.

### FR-10: Export MP4

The system shall export a final MP4 between 60 and 180 seconds.

**Acceptance criteria:**

- output opens in a standard player;
- duration is within the required range;
- no obvious black-frame or encoding failure occurs;
- synchronisation error at the clap verification point should be no more than **±100 milliseconds**, unless the team justifies another threshold.

### FR-11: Human Review

The output shall remain a draft until a human reviewer approves it.

**Acceptance criteria:**

- a review checklist exists;
- the draft filename clearly contains `draft`;
- review comments or approval are recorded.

---

## 12. EDL Specification

Example:

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
      "action": "cut"
    }
  ]
}
```

### EDL Rules

- `start` and `end` use the synchronised master timeline.
- `end` must be greater than `start`.
- `camera` must identify an available source.
- `reason` must explain why the camera was chosen.
- supported actions in the minimum prototype are:
  - `cut`;
  - `fade_in`;
  - `fade_out`;
  - `fade_to_black`.
- crossfade is optional and excluded from the minimum version.
- overlapping segments are not supported in the minimum version.
- total duration must be 60–180 seconds.
- at least two cameras and three switches must be present.

---

## 13. Non-Functional Requirements

### NFR-01: Explainability

Every camera decision must include a human-readable reason.

### NFR-02: Privacy

Use simulated footage unless written permission exists.

### NFR-03: Local Processing

Raw footage should remain local unless the team has explicit permission and a justified secure workflow.

### NFR-04: Reliability

Errors must be visible and understandable.

### NFR-05: Reproducibility

Another teammate should be able to run the project using the README and provided files.

### NFR-06: Maintainability

Validation, synchronisation, EDL parsing, rendering, and review should be separated logically.

### NFR-07: Honest Capability Description

The documentation must distinguish:

- manual work;
- rule-based automation;
- actual AI or machine-learning components;
- human review.

---

## 14. Suggested Project Structure

```text
kindergarten-video-pipeline/
├── README.md
├── PRD.md
├── architecture.md
├── requirements.txt
├── input/
├── config/
│   └── sync.json
├── edl/
│   └── editing_decisions.json
├── src/
│   ├── main.py
│   ├── validate_inputs.py
│   ├── sync.py
│   ├── edl.py
│   ├── renderer.py
│   └── review.py
├── tests/
├── output/
└── evidence/
```

`design.md` is only required if the team decides to create a user interface.

---

## 15. Testing Plan

### 15.1 Unit Tests

- valid EDL loads;
- invalid JSON is rejected;
- missing camera is rejected;
- invalid time ranges are rejected;
- offsets are calculated correctly;
- unsupported actions are rejected.

### 15.2 Integration Tests

- two cameras and one EDL render successfully;
- at least three switches are present;
- title, lower-third, transition, and credits appear;
- final duration is valid;
- output MP4 opens successfully.

### 15.3 Synchronisation Test

- verify the clap point visually or audibly;
- confirm the synchronisation difference is within the selected threshold;
- record the result in the test evidence.

### 15.4 Manual Review

- inspect every camera switch;
- check that important moments remain;
- check audio continuity;
- check text readability;
- confirm privacy and copyright requirements.

---

## 16. Privacy, Legal, and Professional Requirements

### 16.1 Children’s Privacy

- use simulated footage for the assignment;
- restrict access to raw footage;
- avoid public cloud AI uploads;
- delete temporary files after the agreed retention period.

### 16.2 Parental Consent

Real-world consent should separately cover:

- recording;
- editing;
- AI-assisted processing;
- private distribution;
- public distribution.

### 16.3 Malaysia PDPA 2010

The report must discuss whether faces, voices, names, uniforms, and other identifying information can identify a child directly or indirectly.

### 16.4 Copyright

- use original, licensed, or royalty-free music;
- record the source and licence;
- do not assume public-upload permission.

### 16.5 AI and Professional Responsibility

- software may select poor camera angles;
- automated editing may remove important moments;
- human review is compulsory;
- capability claims must remain accurate.

### 16.6 Software Licensing

Record the licences of:

- MoviePy;
- FFmpeg;
- fonts;
- music;
- any additional packages.

---

## 17. PRD Review Plan for the One-Week Period

| Day | PRD Activity | Output |
|---|---|---|
| Day 1 | Read assignment and identify required deliverables | Initial notes and requirement list |
| Day 2 | Discuss scope and tools with the first AI | PRD Draft v1 |
| Day 3 | Give PRD Draft v1 to a second AI or agent | Critical review |
| Day 4 | Answer reviewer questions and resolve contradictions | Decision log |
| Day 5 | Revise scope, requirements, risks, and testing | PRD Draft v2 |
| Day 6 | Final team review and lecturer-question list | Near-final PRD |
| Day 7 | Approve and freeze the PRD | Final `PRD.md` |

Implementation begins only after the PRD is approved.

---

## 18. PRD Definition of Done

The PRD is complete when:

- the official project purpose is clear;
- one synchronisation method is selected;
- one rendering method is selected;
- one optional automation method is selected;
- functional requirements are testable;
- the EDL format is defined;
- mandatory prototype requirements are included;
- privacy and legal requirements are included;
- out-of-scope items are explicit;
- risks and fallback options are documented;
- another AI or agent has grilled the PRD;
- the team has responded to the critique;
- unresolved lecturer questions are listed;
- the team approves the final version.

---

## 19. Questions Requiring Lecturer Confirmation

1. Does the one-week instruction apply only to PRD preparation and review?
2. Does the original prototype implementation schedule remain unchanged?
3. Is the official project title required even if the chosen prototype uses rule-based automation rather than machine learning?
4. Is a rule-based camera-switching method sufficient for the automation component?
5. Does the unrelated KinderSort, Ollama, low-resource PC, and Windows installer rubric apply to this project?
6. Is a demo recording required in addition to the final MP4 or repository?
7. Will the lecturer provide the starter video pack?

---

## 20. Prompt for the Next AI Review Round

```text
Act as an experienced software architect, senior programmer, QA engineer, and privacy-aware reviewer.

Review this revised PRD for the official assignment titled “AI-Assisted Multi-Camera Kindergarten Graduation Video Editing Pipeline.”

Important clarification:
- the one-week duration applies to PRD discussion, critique, revision, and approval;
- it does not automatically mean the whole prototype must be completed in one week.

Check whether the revised PRD now resolves:
1. the AI-assisted title versus rule-based automation issue;
2. the MoviePy risk by providing an FFmpeg fallback;
3. the vague synchronisation acceptance criterion;
4. the transition and crossfade ambiguity;
5. the separation between the PRD timeline and the implementation timeline.

Continue grilling the PRD. Ask one important question at a time. Do not rewrite the document until the discussion is complete.

At the end, provide:
- unresolved issues;
- required amendments;
- optional improvements;
- and a final verdict: APPROVE, APPROVE WITH CHANGES, or REJECT.
```
