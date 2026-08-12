import { CheckSquare2 } from "lucide-react";

export const reviewItems = [
  ["output_opens", "Draft opens and plays completely"],
  ["duration_valid", "Output duration matches the configured policy"],
  ["clap_sync_within_threshold", "Clap synchronisation is within ±100 ms"],
  ["two_cameras_visible", "At least two camera views are visible"],
  ["three_switches_visible", "At least three camera switches are visible"],
  ["title_readable", "Opening title is readable"],
  ["credits_readable", "Closing credits are readable"],
  ["overlay_readable", "Lower-third or label is readable"],
  ["transition_visible", "At least one transition is visible"],
  ["important_moments_retained", "Important ceremony moments are retained"],
  ["camera_choices_reasonable", "Camera choices are reasonable"],
  ["audio_continuity_acceptable", "Audio continuity is acceptable"],
  ["privacy_checked", "Privacy has been checked"],
  ["asset_licences_checked", "Asset licences have been checked"],
] as const;

export type ReviewChecklistState = Record<
  (typeof reviewItems)[number][0],
  boolean
>;

export const emptyChecklist = () =>
  Object.fromEntries(
    reviewItems.map(([key]) => [key, false]),
  ) as ReviewChecklistState;

export function isReviewChecklistState(
  value: unknown,
): value is ReviewChecklistState {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const record = value as Record<string, unknown>;
  return reviewItems.every(([key]) => typeof record[key] === "boolean");
}

export function ReviewChecklist({
  values,
  onChange,
}: {
  values: ReviewChecklistState;
  onChange: (values: ReviewChecklistState) => void;
}) {
  const completed = Object.values(values).filter(Boolean).length;
  return (
    <fieldset>
      <legend className="mb-4 flex w-full items-center justify-between">
        <span className="flex items-center gap-2 font-bold">
          <CheckSquare2 className="h-5 w-5 text-primary" /> Complete playback
          checklist
        </span>
        <span className="text-sm text-ink-muted">
          {completed}/{reviewItems.length}
        </span>
      </legend>
      <div className="grid gap-2 sm:grid-cols-2">
        {reviewItems.map(([key, label]) => (
          <label
            key={key}
            className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-sm ${values[key] ? "border-success/40 bg-success-soft" : "border-border bg-white"}`}
          >
            <input
              type="checkbox"
              className="mt-0.5 h-4 w-4 accent-primary"
              checked={values[key]}
              onChange={(event) =>
                onChange({ ...values, [key]: event.target.checked })
              }
            />
            <span>{label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
