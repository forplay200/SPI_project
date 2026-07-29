import { Camera, Tag } from "lucide-react";

import type { EDLSegment } from "../api/types";

const cameraStyles = [
  "bg-blue-600",
  "bg-emerald-600",
  "bg-violet-600",
  "bg-amber-600",
];

export function EditingTimeline({ segments }: { segments: EDLSegment[] }) {
  const start = segments[0]?.start ?? 0;
  const end = segments.at(-1)?.end ?? 1;
  const total = Math.max(0.001, end - start);
  const cameraIds = [...new Set(segments.map((item) => item.camera))];
  return (
    <div className="overflow-x-auto" aria-label="Simplified editing timeline">
      <div className="min-w-[720px] rounded-xl bg-video p-5 text-white">
        <div className="mb-3 flex h-16 overflow-hidden rounded-lg border border-white/10">
          {segments.map((segment) => {
            const cameraIndex = cameraIds.indexOf(segment.camera);
            return (
              <div
                key={segment.id}
                className={`${cameraStyles[cameraIndex % cameraStyles.length]} relative flex min-w-20 items-center justify-center border-r border-white/20 px-2 text-center text-xs font-bold`}
                style={{
                  width: `${((segment.end - segment.start) / total) * 100}%`,
                }}
                title={`${segment.start.toFixed(2)}–${segment.end.toFixed(2)} s · ${segment.reason}`}
              >
                <Camera className="mr-1 h-3.5 w-3.5" />
                {segment.camera}
                {segment.overlay ? (
                  <Tag className="absolute right-1 top-1 h-3 w-3" />
                ) : null}
              </div>
            );
          })}
        </div>
        <div className="flex justify-between text-xs text-slate-300">
          <span>{start.toFixed(1)} s</span>
          <span>Contiguous master timeline · {segments.length} shots</span>
          <span>{end.toFixed(1)} s</span>
        </div>
      </div>
    </div>
  );
}
