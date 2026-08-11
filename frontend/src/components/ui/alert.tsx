import { AlertCircle, CheckCircle2, Info, TriangleAlert } from "lucide-react";
import type { HTMLAttributes } from "react";

import { cn } from "../../lib/utils";

type Tone = "info" | "success" | "warning" | "danger";

export function Alert({
  tone = "info",
  title,
  children,
  className,
}: HTMLAttributes<HTMLDivElement> & { tone?: Tone; title: string }) {
  const styles = {
    info: "border-primary/25 bg-primary-soft text-primary-hover",
    success: "border-success/25 bg-success-soft text-success",
    warning: "border-warning/25 bg-warning-soft text-amber-900",
    danger: "border-danger/25 bg-danger-soft text-red-900",
  };
  const Icon =
    tone === "success"
      ? CheckCircle2
      : tone === "warning"
        ? TriangleAlert
        : tone === "danger"
          ? AlertCircle
          : Info;
  return (
    <div
      className={cn(
        "flex gap-3 rounded-xl border p-4",
        styles[tone],
        className,
      )}
      role={tone === "danger" ? "alert" : "status"}
    >
      <Icon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
      <div>
        <p className="font-semibold">{title}</p>
        <div className="mt-1 text-sm leading-6">{children}</div>
      </div>
    </div>
  );
}
