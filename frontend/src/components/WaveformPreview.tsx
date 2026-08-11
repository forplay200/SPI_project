import { AudioLines } from "lucide-react";
import { useEffect, useRef } from "react";

export function WaveformPreview({
  mediaUrl,
  timestamp,
}: {
  mediaUrl: string;
  timestamp: number;
}) {
  const media = useRef<HTMLVideoElement>(null);
  useEffect(() => {
    const element = media.current;
    if (!element) return;
    const seek = () => {
      element.currentTime = Math.max(0, timestamp - 2);
    };
    element.addEventListener("loadedmetadata", seek);
    return () => element.removeEventListener("loadedmetadata", seek);
  }, [timestamp]);
  return (
    <div className="rounded-lg bg-video p-3 text-white">
      <div
        className="mb-2 flex h-12 items-center justify-center gap-1 overflow-hidden rounded bg-white/5"
        aria-label="Waveform preview placeholder"
      >
        {[18, 30, 22, 38, 20, 45, 72, 34, 20, 28, 16, 42, 24, 19, 31, 22].map(
          (height, index) => (
            <span
              key={index}
              className="w-1 rounded-full bg-primary-soft/80"
              style={{ height }}
            />
          ),
        )}
        <AudioLines className="ml-3 h-5 w-5 text-primary-soft" />
      </div>
      <video
        ref={media}
        src={mediaUrl}
        controls
        preload="metadata"
        className="h-10 w-full"
        aria-label={`Audio and video preview near ${timestamp.toFixed(3)} seconds`}
      />
      <p className="mt-2 text-xs text-slate-300">
        Preview starts two seconds before the candidate. The waveform is a
        placeholder; use the local media controls for verification.
      </p>
    </div>
  );
}
