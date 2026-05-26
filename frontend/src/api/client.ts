const API_BASE = "/api";

export interface DataTreeFile {
  type: string;
  name: string;
  path: string;
  size_bytes: number;
  extension: string;
  extension_normalized: string;
  format_label: string;
  ingestible: boolean;
  loaded_in_cohort: boolean;
}

export interface DataTreeRoot {
  id: string;
  type: string;
  label: string;
  path: string;
  role: string;
  file_count: number;
  extension_counts: Record<string, number>;
  files: DataTreeFile[];
}

export interface BootstrapResponse {
  auto_loaded: boolean;
  active_folder: string | null;
  cohort_size: number;
  data_tree: {
    app_data_root: string;
    project_data_root: string;
    roots: DataTreeRoot[];
    extension_summary: Record<string, number>;
    supported_ingest_extensions: string[];
  };
}

export interface DicomRecord {
  id: string;
  filename: string;
  file_extension?: string;
  format_label?: string;
  modality: string;
  patient_id: string;
  patient_age_raw: string;
  patient_age_years: number | null;
  patient_sex: string;
  acquisition_date: string;
  body_part: string;
  manufacturer: string;
  rows: number | null;
  cols: number | null;
  bits_allocated: number | null;
  has_pixel_data: boolean;
}

export interface Summary {
  total: number;
  modality_counts: Record<string, number>;
  body_part_counts: Record<string, number>;
  sex_counts: Record<string, number>;
  age_stats: {
    count: number;
    mean: number | null;
    min: number | null;
    max: number | null;
    std: number | null;
  };
  image_size_stats: {
    mean_rows: number | null;
    mean_cols: number | null;
  };
  bits_allocated_counts: Record<string, number>;
  has_pixel_data: number;
  acquisition_year_counts: Record<string, number>;
}

export interface DatasetInfo {
  title: string;
  data_type: string;
  origin: string;
  context: string;
  modalities_expected: string[];
  paths: {
    project_source: string;
    app_mirror: string;
    project_root: string;
  };
  file_counts: { source_folder: number; app_data_folder: number };
  sync_status: { ok: boolean; destination?: string; file_count?: number };
  fields_extracted: string[];
  what_you_see: string[];
}

export interface PlotsResponse {
  available: boolean;
  message?: string;
  cohort_size?: number;
  plots?: Record<string, string>;
  plot_labels?: Record<string, string>;
}

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export async function fetchDatasetInfo(): Promise<DatasetInfo> {
  const res = await fetch(`${API_BASE}/dataset-info`);
  return parseJson(res);
}

export async function fetchBootstrap(): Promise<BootstrapResponse> {
  const res = await fetch(`${API_BASE}/bootstrap`);
  return parseJson(res);
}

export async function fetchPlots(): Promise<PlotsResponse> {
  const res = await fetch(`${API_BASE}/plots`);
  return parseJson(res);
}

export async function uploadFiles(files: FileList): Promise<{ uploaded: number; failed: number }> {
  const form = new FormData();
  Array.from(files).forEach((f) => form.append("files", f));
  const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: form });
  return parseJson(res);
}

export async function scanSampleFolder(): Promise<{ loaded: number; scanned: number; folder?: string }> {
  const res = await fetch(`${API_BASE}/scan-folder`, { method: "POST" });
  return parseJson(res);
}

export async function fetchRecords(): Promise<{ total: number; records: DicomRecord[] }> {
  const res = await fetch(`${API_BASE}/records`);
  return parseJson(res);
}

export async function fetchSummary(): Promise<Summary> {
  const res = await fetch(`${API_BASE}/summary`);
  return parseJson(res);
}

export async function fetchThumbnail(id: string): Promise<string | null> {
  try {
    const res = await fetch(`${API_BASE}/image/${id}`);
    if (!res.ok) return null;
    const data = await res.json();
    return data.thumbnail_b64 as string;
  } catch {
    return null;
  }
}

export async function clearRecords(): Promise<void> {
  await fetch(`${API_BASE}/clear`, { method: "DELETE" });
}
