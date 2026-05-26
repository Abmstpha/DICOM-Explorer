import type { Summary } from "../api/client";

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span className="metric-label">{label}</span>
      <span className="metric-value">{value}</span>
    </div>
  );
}

export function SummaryPanel({ summary }: { summary: Summary }) {
  const age = summary.age_stats;
  const ageStr =
    age.count > 0 ? `${age.mean} ± ${age.std} yr (range ${age.min}–${age.max}, n=${age.count})` : "Not available in cohort";

  return (
    <section className="panel" id="summary">
      <div className="section-label">§ 2 — Descriptive statistics</div>
      <h2>
        Summary statistics <span className="badge">n = {summary.total}</span>
      </h2>
      <div className="metrics-row">
        <Metric label="Instances" value={String(summary.total)} />
        <Metric label="With pixel data" value={String(summary.has_pixel_data)} />
        <Metric
          label="Mean matrix size"
          value={
            summary.image_size_stats.mean_rows != null
              ? `${summary.image_size_stats.mean_rows} × ${summary.image_size_stats.mean_cols} px`
              : "—"
          }
        />
        <Metric label="Patient age" value={ageStr} />
      </div>
      <p className="muted note">
        Descriptive statistics computed across all loaded DICOM instances in the cohort.
      </p>
    </section>
  );
}
