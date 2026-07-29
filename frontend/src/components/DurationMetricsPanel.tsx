import { Card, CardContent } from "./ui/card";

type DurationMetricsPanelProps = {
  commonOverlap: number | null | undefined;
  eventCoverage: number | null | undefined;
  maximumRenderable: number | null | undefined;
};

const seconds = (value: number | null | undefined) =>
  value == null ? "Pending sync analysis" : `${value.toFixed(2)} s`;

export function DurationMetricsPanel({
  commonOverlap,
  eventCoverage,
  maximumRenderable,
}: DurationMetricsPanelProps) {
  const metrics = [
    {
      label: "Common Synchronized Overlap",
      value: commonOverlap,
      explanation:
        "Time covered by every selected camera. This informs sync quality only; it is not the edit-duration limit.",
    },
    {
      label: "Total Event Coverage",
      value: eventCoverage,
      explanation:
        "The union of synchronized camera timelines, including intervals covered by only one camera.",
    },
    {
      label: "Maximum Renderable Duration",
      value: maximumRenderable,
      explanation:
        "Longest output supported by a valid per-shot camera assignment, source boundaries, and switching rules.",
    },
  ];
  return (
    <div className="grid gap-4 lg:grid-cols-3" aria-label="Duration metrics">
      {metrics.map((metric) => (
        <Card key={metric.label}>
          <CardContent>
            <p className="text-sm font-semibold text-ink-muted">
              {metric.label}
            </p>
            <p className="mt-1 text-2xl font-bold">{seconds(metric.value)}</p>
            <p className="mt-2 text-xs leading-5 text-ink-muted">
              {metric.explanation}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
