import { useEffect, useState } from "react";
import { fetchPlots, type PlotsResponse } from "../api/client";

const ORDER = [
  "modality_distribution",
  "body_part_distribution",
  "sex_distribution",
  "age_histogram",
  "bits_allocated",
  "pixel_by_modality",
];

export function AnalysisCharts({ cohortSize }: { cohortSize: number }) {
  const [data, setData] = useState<PlotsResponse | null>(null);

  useEffect(() => {
    if (cohortSize <= 0) {
      setData(null);
      return;
    }
    fetchPlots().then(setData).catch(() => setData({ available: false, message: "Plot generation failed" }));
  }, [cohortSize]);

  if (cohortSize <= 0) {
    return (
      <section className="panel" id="figures">
        <div className="section-label">§ 3 — Statistical figures</div>
        <h2>Cohort analytics</h2>
        <p className="muted">Load the DICOM corpus to generate matplotlib figures from extracted metadata.</p>
      </section>
    );
  }

  if (!data?.available || !data.plots) {
    return (
      <section className="panel" id="figures">
        <div className="section-label">§ 3 — Statistical figures</div>
        <h2>Cohort analytics</h2>
        <p className="muted">{data?.message ?? "Generating plots…"}</p>
      </section>
    );
  }

  const keys = ORDER.filter((k) => data.plots![k]);

  return (
    <section className="panel" id="figures">
      <div className="section-label">§ 3 — Statistical figures</div>
      <h2>Cohort analytics <span className="badge">n = {data.cohort_size}</span></h2>
      <p className="muted">
        Distribution of key DICOM fields across the loaded cohort.
      </p>
      <div className="figure-grid">
        {keys.map((key) => (
          <figure key={key} className="figure-card">
            <figcaption>{data.plot_labels?.[key] ?? key}</figcaption>
            <img
              src={`data:image/png;base64,${data.plots![key]}`}
              alt={data.plot_labels?.[key] ?? key}
            />
          </figure>
        ))}
      </div>
    </section>
  );
}
