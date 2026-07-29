export type Project = {
  id: string;
  title: string;
  input_folder: string;
  duration_seconds: number;
  resolution: "1280x720" | "1920x1080";
  draft_mode: boolean;
  smoke_mode: boolean;
  credits: string;
  credits_duration: number | null;
  created_at: string;
  updated_at: string;
  outcome: string;
  current_step: number;
  artifacts: Record<string, string>;
  latest_job_id: string | null;
};

export type JobStatus =
  | "QUEUED"
  | "DISCOVERING"
  | "PROBING_MEDIA"
  | "GROUPING_CAMERAS"
  | "ANALYSING_AUDIO"
  | "GENERATING_EDL"
  | "VALIDATING"
  | "RENDERING"
  | "VALIDATING_OUTPUT"
  | "GENERATING_EVIDENCE"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export type Job = {
  job_id: string;
  project_id: string;
  operation: string;
  status: JobStatus;
  progress: number;
  message: string;
  current_step: number;
  warning: string | null;
  error: string | null;
  result: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type DiscoveredVideo = {
  camera_id: string | null;
  relative_path: string;
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
  display_rotation: number;
  fps: number | null;
  video_codec: string | null;
  has_audio: boolean | null;
  audio_codec: string | null;
  classification: string;
  usable: boolean;
  warnings: string[];
};

export type PairScore = {
  camera_a: string;
  camera_b: string;
  path_a: string;
  path_b: string;
  audio_correlation: number;
  estimated_offset_seconds: number | null;
  offset_stability: number;
  shared_transient_count: number;
  common_usable_duration_seconds: number;
  derived_duplicate_likelihood: number;
  total_score: number;
  confidence: string;
  accepted: boolean;
  suggested?: boolean;
  reason: string;
};

export type DurationMetrics = {
  common_overlap_duration: number | null;
  total_event_coverage: number | null;
  maximum_renderable_duration: number | null;
};

export type Analysis = {
  videos: DiscoveredVideo[];
  selected_camera_ids: string[];
  master_camera: string | null;
  suggested_camera_ids: string[];
  suggested_master_camera: string | null;
  grouping: {
    state: string;
    confidence: string;
    reason: string;
    best_score: number | null;
    analysed_pair_count: number;
    pair_scores: PairScore[];
    selected_videos?: DiscoveredVideo[];
  };
  common_overlap_duration: number | null;
  total_event_coverage: number | null;
  maximum_renderable_duration: number | null;
};

export type SyncCandidate = {
  timestamp_seconds: number;
  confidence: number;
  cue_type: string;
  supporting_metric: number;
};

export type SyncAnalysis = {
  camera_id: string;
  candidates: SyncCandidate[];
  selected_timestamp_seconds: number | null;
  confidence: number;
  state: string;
  requires_human_verification: boolean;
  warnings: string[];
};

export type SyncReport = {
  master_camera: string;
  cue_type: string;
  cue_description: string;
  acceptance_status: string;
  clap_timestamps: Record<string, number>;
  verification_threshold_ms: number;
  requires_human_verification: boolean;
  camera_analyses: SyncAnalysis[];
  manual_confirmations: Record<
    string,
    {
      timestamp_seconds: number;
      state: string;
      sync_risk_acknowledged?: boolean;
    }
  >;
  pairwise_alignment?: Array<{
    camera_a: string;
    camera_b: string;
    state: string;
    selected_offset_seconds: number | null;
    reason: string;
    alternatives: Array<{
      offset_seconds: number;
      confidence: number;
      audio_correlation: number;
      overlap_seconds: number;
      overlap_ratio: number;
      offset_stability: number;
      supported_windows: number;
      large_offset: boolean;
      accepted_for_automatic_use: boolean;
      reason: string;
    }>;
  }>;
  sync_sanity?: {
    status: string;
    common_usable_duration_seconds: number | null;
    zero_offset_common_duration_seconds: number | null;
    overlap_preservation_ratio: number | null;
    warnings: string[];
  };
  duration_metrics?: DurationMetrics;
};

export type Overlay = {
  type: "lower_third" | "label" | "subtitle";
  text: string;
  start?: number;
  end?: number;
  position?: string;
};

export type EDLSegment = {
  id: string;
  start: number;
  end: number;
  camera: string;
  reason: string;
  action: "cut" | "fade_in" | "fade_out" | "fade_to_black";
  overlay?: Overlay;
};

export type EDL = {
  project: string;
  timeline: EDLSegment[];
  common_overlap_duration?: number | null;
  total_event_coverage?: number | null;
  maximum_renderable_duration?: number | null;
};

export type Draft = {
  path: string;
  filename: string;
  sha256: string;
  metadata: {
    duration_seconds: number;
    width: number;
    height: number;
    fps: number;
    has_video: boolean;
    has_audio: boolean;
    video_codec: string | null;
    audio_codec: string | null;
  };
  renderer_used: string;
  sync_state: string;
  compliance_state: string;
  human_review_required: boolean;
  common_overlap_duration: number | null;
  total_event_coverage: number | null;
  maximum_renderable_duration: number | null;
};

export type Approval = {
  eligible: boolean;
  blockers: string[];
  draft_sha256: string | null;
  review_status: string;
  sync_status: string;
  compliance_status: string;
};

export type EvidenceItem = {
  id: string;
  label: string;
  category: string;
  path: string;
  media_type: string;
  exists: boolean;
};
