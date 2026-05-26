import type { DataTreeRoot } from "../api/client";

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function FolderBlock({ root }: { root: DataTreeRoot }) {
  return (
    <div className="folder-block">
      <div className="folder-head">
        <span className="folder-icon">📁</span>
        <div>
          <strong>{root.label}</strong>
          <span className={`role-badge role-${root.role}`}>{root.role}</span>
          <span className="muted"> · {root.file_count} files</span>
        </div>
      </div>
      {Object.keys(root.extension_counts).length > 0 && (
        <div className="ext-summary">
          {Object.entries(root.extension_counts).map(([ext, n]) => (
            <span key={ext} className="ext-chip">
              <code>{ext}</code> × {n}
            </span>
          ))}
        </div>
      )}
      <div className="file-list-wrap">
        <table className="data-table file-table">
          <thead>
            <tr>
              <th>File</th>
              <th>Extension</th>
              <th>Format</th>
              <th>Size</th>
              <th>Cohort</th>
            </tr>
          </thead>
          <tbody>
            {root.files.map((f) => (
              <tr key={f.path} className={f.loaded_in_cohort ? "row-loaded" : ""}>
                <td className="fname">{f.name}</td>
                <td>
                  <code className="ext-badge">{f.extension}</code>
                </td>
                <td>{f.format_label}</td>
                <td>{formatBytes(f.size_bytes)}</td>
                <td>{f.loaded_in_cohort ? "✓ loaded" : f.ingestible ? "—" : "n/a"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function FileTreePanel({
  roots,
  extensionSummary,
  supported,
  cohortSize,
  autoLoaded,
}: {
  roots: DataTreeRoot[];
  extensionSummary: Record<string, number>;
  supported: string[];
  cohortSize: number;
  autoLoaded: boolean;
}) {
  return (
    <section className="panel" id="filesystem">
      <div className="section-label">§ 1b — Data repository (on disk)</div>
      <h2>
        Files &amp; folders{" "}
        <span className="badge">{cohortSize} ingested</span>
      </h2>
      {autoLoaded && (
        <p className="status ok-banner">
          Corpus <strong>auto-loaded on server start</strong> from the bundled DICOM folder — no upload required.
        </p>
      )}
      <p className="muted">
        Supported ingest extensions:{" "}
        {supported.map((e) => (
          <code key={e} className="inline-code">
            {e}
          </code>
        ))}{" "}
        · Project-wide extension counts:{" "}
        {Object.entries(extensionSummary).map(([ext, n]) => (
          <span key={ext}>
            <code>{ext}</code>({n}){" "}
          </span>
        ))}
      </p>
      {roots.map((root) => (
        <FolderBlock key={root.id} root={root} />
      ))}
    </section>
  );
}
