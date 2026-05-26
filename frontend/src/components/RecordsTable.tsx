import { useEffect, useState } from "react";
import { fetchThumbnail, type DicomRecord } from "../api/client";

function Thumbnail({ id }: { id: string }) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchThumbnail(id).then((b64) => {
      if (!cancelled && b64) setSrc(`data:image/png;base64,${b64}`);
    });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (!src) return <div className="thumb" />;
  return <img className="thumb" src={src} alt="" />;
}

export function RecordsTable({ records }: { records: DicomRecord[] }) {
  if (records.length === 0) {
    return (
      <section className="panel">
        <div className="section-label">§ 4 — Metadata registry</div>
        <h2>Records</h2>
        <p style={{ color: "#64748b", margin: 0 }}>
          No DICOM records yet. Upload files or click &quot;Load sample folder&quot;.
        </p>
      </section>
    );
  }

  return (
    <section className="panel" id="registry">
      <div className="section-label">§ 4 — Metadata registry</div>
      <h2>
        Instance-level metadata <span className="badge">n = {records.length}</span>
      </h2>
      <p className="muted">One row per DICOM file with extracted clinical metadata.</p>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th></th>
              <th>File</th>
              <th>Ext</th>
              <th>Modality</th>
              <th>Age</th>
              <th>Sex</th>
              <th>Acquisition date</th>
              <th>Body part</th>
              <th>Size</th>
            </tr>
          </thead>
          <tbody>
            {records.map((r) => (
              <tr key={r.id}>
                <td>
                  <Thumbnail id={r.id} />
                </td>
                <td title={r.filename}>{r.filename.length > 24 ? `${r.filename.slice(0, 21)}…` : r.filename}</td>
                <td><code>{r.file_extension ?? "—"}</code></td>
                <td>{r.modality}</td>
                <td>{r.patient_age_raw !== "N/A" ? r.patient_age_raw : "—"}</td>
                <td>{r.patient_sex}</td>
                <td>{r.acquisition_date}</td>
                <td>{r.body_part}</td>
                <td>
                  {r.rows && r.cols ? `${r.rows}×${r.cols}` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
