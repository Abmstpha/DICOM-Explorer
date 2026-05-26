import { useEffect, useState } from "react";
import { fetchDatasetInfo, type DatasetInfo } from "../api/client";

export function DataSourcePanel() {
  const [info, setInfo] = useState<DatasetInfo | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    fetchDatasetInfo()
      .then(setInfo)
      .catch((e) => setErr(e instanceof Error ? e.message : "Could not load dataset information."));
  }, []);

  if (err) {
    return (
      <section className="panel panel-accent">
        <p className="status error">{err}</p>
      </section>
    );
  }
  if (!info) {
    return (
      <section className="panel panel-accent">
        <p className="muted">Loading…</p>
      </section>
    );
  }

  return (
    <section className="panel panel-accent" id="dataset">
      <div className="section-label">§ 1 — About this dataset</div>
      <h2>Sample imaging corpus</h2>

      <div className="prose-grid">
        <div>
          <h3>Format</h3>
          <p>
            <strong>{info.data_type}</strong> — multi-modality collection (CT, MRI, ultrasound,
            nuclear medicine, radiotherapy, and more).
          </p>
        </div>
        <div>
          <h3>Modalities in this collection</h3>
          <p className="tag-row">
            {info.modalities_expected.map((m) => (
              <span key={m} className="tag">
                {m}
              </span>
            ))}
          </p>
        </div>
        <div>
          <h3>Volume</h3>
          <p>
            <strong>{info.file_counts.app_data_folder}</strong> DICOM files in the bundled sample folder
            (<code>data/DICOM_samples</code>).
          </p>
        </div>
        <div>
          <h3>Metadata fields</h3>
          <ul className="compact-list">
            {info.fields_extracted.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
        </div>
      </div>

      <h3 className="subhead">What this explorer shows</h3>
      <ul className="compact-list overview-list">
        {info.what_you_see.map((t) => (
          <li key={t}>{t}</li>
        ))}
      </ul>
    </section>
  );
}
