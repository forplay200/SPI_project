# ADR 0001: Coverage-Based Renderability

- Status: Accepted
- Date: 2026-07-29

## Context

The automatic EDL generator previously treated the intersection of every
selected camera timeline as the maximum output duration. The renderer and manual
EDL workflow instead validate only the camera assigned to each segment. This
made automatic generation reject valid event-coverage edits when cameras started
or stopped at different times.

## Decision

Renderability is determined by available synchronized camera coverage and valid
EDL construction, not by all-camera synchronized overlap.

The pipeline exposes three distinct metrics:

- `common_overlap_duration`: intersection of all selected synchronized camera
  timelines. It is a synchronization diagnostic and never the render limit.
- `total_event_coverage`: union of all synchronized camera timelines, including
  intervals covered by one camera.
- `maximum_renderable_duration`: longest output for which the deterministic
  generator can assign every shot to a camera that covers it while preserving
  source boundaries, minimum-shot policy, at least two cameras, at least three
  switches, required transitions, and presentation screens.

The EDL timeline remains non-negative. Camera coverage before master time zero is
included in total event coverage but is not silently rebased; changing the time
origin requires an explicit synchronization-model decision.

The generator rejects only when the requested output exceeds
`maximum_renderable_duration` or no valid camera sequence can satisfy the
existing EDL contract. Semantic EDL validation and renderer-neutral source
boundary validation remain authoritative.

## Consequences

- Automatic EDLs may legitimately exceed common synchronized overlap.
- A camera need not cover the complete project; it must cover only its assigned
  segments.
- Disconnected event coverage is not treated as continuous renderable footage.
- The former `INSUFFICIENT_COMMON_DURATION` outcome is replaced by
  `INSUFFICIENT_RENDERABLE_DURATION`.
- Evidence, API responses, CLI summaries, and the guided UI report all three
  metrics so users can distinguish sync quality from edit capacity.
