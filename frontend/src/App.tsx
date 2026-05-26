import { useCallback, useEffect, useState } from "react";
import {
  clearRecords,
  fetchBootstrap,
  fetchRecords,
  fetchSummary,
  scanSampleFolder,
  type BootstrapResponse,
  type DicomRecord,
  type Summary,
} from "./api/client";
import { AnalysisCharts } from "./components/AnalysisCharts";
import { DataSourcePanel } from "./components/DataSourcePanel";
import { FileTreePanel } from "./components/FileTreePanel";
import { RecordsTable } from "./components/RecordsTable";
import { SummaryPanel } from "./components/SummaryPanel";

export default function App() {
  const [records, setRecords] = useState<DicomRecord[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [bootstrap, setBootstrap] = useState<BootstrapResponse | null>(null);
  const [status, setStatus] = useState("Loading…");
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const [boot, recData, sumData] = await Promise.all([
      fetchBootstrap(),
      fetchRecords(),
      fetchSummary(),
    ]);
    setBootstrap(boot);
    setRecords(recData.records);
    setSummary(sumData.total > 0 ? sumData : null);
    if (boot.auto_loaded) {
      setStatus(
        `Ready — ${boot.cohort_size} DICOM file(s) auto-loaded from ${boot.active_folder ?? "APP/data/DICOM_samples"}.`
      );
      setError(false);
    } else if (recData.total === 0) {
      setStatus("No DICOM files loaded — restart the application.");
    }
  }, []);

  useEffect(() => {
    refresh()
      .catch((e) => {
        setError(true);
        setStatus(e instanceof Error ? e.message : "Cannot connect — start the application server first.");
      })
      .finally(() => setLoading(false));
  }, [refresh]);

  const onReload = async () => {
    setLoading(true);
    setError(false);
    setStatus("Reloading corpus from disk…");
    try {
      const res = await scanSampleFolder();
      await refresh();
      setStatus(`Reloaded ${res.loaded} file(s) from disk.`);
    } catch (e) {
      setError(true);
      setStatus(e instanceof Error ? e.message : "Reload failed");
    } finally {
      setLoading(false);
    }
  };

  const onClear = async () => {
    setLoading(true);
    try {
      await clearRecords();
      await refresh();
      setStatus("Cohort cleared. Click Reload to ingest again.");
      setError(false);
    } catch (e) {
      setError(true);
      setStatus(e instanceof Error ? e.message : "Clear failed");
    } finally {
      setLoading(false);
    }
  };

  const tree = bootstrap?.data_tree;

  return (
    <div className="app">
      <header className="site-header">
        <div className="header-inner">
          <p className="course-line">AI for Health · PGE5</p>
          <h1>DICOM Metadata Explorer</h1>
          <p className="subtitle">
            Explore DICOM metadata across a multi-modality teaching corpus — summary statistics,
            charts, and a full instance registry. Data load automatically when you open this page.
          </p>
        </div>
      </header>

      {status && (
        <p className={`status banner ${error ? "error" : ""}`}>{loading ? "… " : ""}{status}</p>
      )}

      <DataSourcePanel />

      {tree && (
        <FileTreePanel
          roots={tree.roots}
          extensionSummary={tree.extension_summary}
          supported={tree.supported_ingest_extensions}
          cohortSize={bootstrap?.cohort_size ?? 0}
          autoLoaded={bootstrap?.auto_loaded ?? false}
        />
      )}

      <section className="panel panel-actions">
        <div className="section-label">§ 1c — Cohort control</div>
        <h2>Reload (optional)</h2>
        <p className="muted">Data are already loaded when the page opens. Use reload only after changing files on disk.</p>
        <div className="actions">
          <button type="button" className="primary" disabled={loading} onClick={onReload}>
            Reload corpus from disk
          </button>
          <button type="button" className="ghost" disabled={loading} onClick={onClear}>
            Clear cohort
          </button>
        </div>
      </section>

      {summary && <SummaryPanel summary={summary} />}
      <AnalysisCharts cohortSize={summary?.total ?? 0} />
      <RecordsTable records={records} />
    </div>
  );
}
