"""
DICOM Metadata Explorer — FastAPI Backend
=========================================
Endpoints:
  POST /upload      — upload one or more DICOM files, extract metadata
  GET  /records     — return all processed records as JSON
  GET  /summary     — aggregated statistics
  GET  /image/{id}  — return a PNG preview of the pixel data (if available)
  DELETE /clear     — wipe the in-memory store
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import pydicom
import pandas as pd
import numpy as np
import io, base64, os, json, tempfile, glob
from typing import List, Optional
from PIL import Image
import warnings

from pathlib import Path

from dataset import (
    classify_extension,
    default_scan_folder,
    display_path,
    get_data_tree,
    get_dataset_catalog,
    iter_dicom_paths,
    sync_dicom_to_app,
)
from plots import generate_plot_bundle

warnings.filterwarnings("ignore")

app = FastAPI(
    title="DICOM Metadata Explorer",
    version="2.0.0",
    description="PGE5 Day 1 Task 2 — pydicom metadata extraction, pandas summaries, publication-style plots",
)


def _ingest_folder(folder_path: str, reset: bool = True) -> dict:
    """Load all DICOM files from folder into cohort."""
    global _loaded_folder, _auto_loaded
    if reset:
        _records.clear()
        _images.clear()

    folder = Path(folder_path)
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail=f"Folder not found: {folder_path}")

    paths = iter_dicom_paths(folder)
    if not paths:
        raise HTTPException(status_code=404, detail="No DICOM files in folder.")

    results, errors = [], []
    for path in paths:
        path_str = str(path)
        try:
            record_id = f"rec_{len(_records) + len(results):04d}"
            meta = _extract_metadata(path_str, record_id)
            ext_info = classify_extension(path.name)
            meta["source_rel"] = display_path(path_str)
            meta["file_extension"] = ext_info["extension"]
            meta["format_label"] = ext_info["format_label"]
            thumbnail = _generate_thumbnail(path_str)
            _records.append(meta)
            if thumbnail:
                _images[record_id] = thumbnail
            results.append({"status": "ok", "id": record_id, "filename": path.name})
        except Exception as e:
            errors.append({"filename": path.name, "error": str(e)})

    _loaded_folder = folder_path
    _auto_loaded = True
    return {
        "folder": display_path(folder_path),
        "scanned": len(paths),
        "loaded": len(results),
        "failed": len(errors),
        "records": results,
        "errors": errors[:20],
    }


@app.on_event("startup")
def _startup_sync_and_load():
    sync_dicom_to_app(force=False)
    try:
        _ingest_folder(default_scan_folder(), reset=True)
    except HTTPException:
        pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory store ──────────────────────────────────────────────────────────
_records: List[dict] = []
_images: dict = {}   # record_id → base64 PNG
_loaded_folder: Optional[str] = None
_auto_loaded: bool = False


def _parse_age(age_str: Optional[str]) -> Optional[float]:
    """Convert DICOM PatientAge string (e.g. '024Y', '006M') to years."""
    if not age_str or age_str == "N/A":
        return None
    age_str = str(age_str).strip()
    try:
        if age_str.endswith("Y"):
            return float(age_str[:-1])
        elif age_str.endswith("M"):
            return float(age_str[:-1]) / 12
        elif age_str.endswith("D"):
            return float(age_str[:-1]) / 365
        else:
            return float(age_str)
    except Exception:
        return None


def _safe_str(val) -> str:
    if val is None:
        return "N/A"
    s = str(val).strip()
    return s if s else "N/A"


def _extract_metadata(path: str, record_id: str) -> dict:
    ds = pydicom.dcmread(path, stop_before_pixels=True, force=True)

    age_raw = _safe_str(getattr(ds, "PatientAge", None))
    age_years = _parse_age(age_raw)

    acq_date_raw = _safe_str(getattr(ds, "AcquisitionDate", None))
    study_date_raw = _safe_str(getattr(ds, "StudyDate", None))
    acq_date = acq_date_raw if acq_date_raw != "N/A" else study_date_raw

    # Format YYYYMMDD → YYYY-MM-DD
    if len(acq_date) == 8 and acq_date.isdigit():
        acq_date = f"{acq_date[:4]}-{acq_date[4:6]}-{acq_date[6:]}"

    rows = getattr(ds, "Rows", None)
    cols = getattr(ds, "Columns", None)
    bits = getattr(ds, "BitsAllocated", None)
    slices = getattr(ds, "NumberOfFrames", None)
    ext_info = classify_extension(os.path.basename(path))

    return {
        "id": record_id,
        "filename": os.path.basename(path),
        "file_extension": ext_info["extension"],
        "format_label": ext_info["format_label"],
        "modality": _safe_str(getattr(ds, "Modality", None)),
        "patient_id": _safe_str(getattr(ds, "PatientID", None)),
        "patient_age_raw": age_raw,
        "patient_age_years": age_years,
        "patient_sex": _safe_str(getattr(ds, "PatientSex", None)),
        "acquisition_date": acq_date,
        "body_part": _safe_str(getattr(ds, "BodyPartExamined", None)),
        "institution": _safe_str(getattr(ds, "InstitutionName", None)),
        "manufacturer": _safe_str(getattr(ds, "Manufacturer", None)),
        "study_description": _safe_str(getattr(ds, "StudyDescription", None)),
        "series_description": _safe_str(getattr(ds, "SeriesDescription", None)),
        "rows": int(rows) if rows is not None else None,
        "cols": int(cols) if cols is not None else None,
        "bits_allocated": int(bits) if bits is not None else None,
        "number_of_frames": int(slices) if slices is not None else None,
        "sop_class_uid": _safe_str(getattr(ds, "SOPClassUID", None)),
        "transfer_syntax": _safe_str(getattr(ds, "file_meta", {}).TransferSyntaxUID if hasattr(ds, "file_meta") and hasattr(ds.file_meta, "TransferSyntaxUID") else None),
        "has_pixel_data": hasattr(ds, "PixelData") or False,
    }


def _generate_thumbnail(path: str) -> Optional[str]:
    """Read pixel data and return a base64-encoded PNG thumbnail, or None."""
    try:
        ds = pydicom.dcmread(path, force=True)
        if not hasattr(ds, "pixel_array"):
            return None
        arr = ds.pixel_array
        if arr.ndim == 3 and arr.shape[0] > 1:
            arr = arr[arr.shape[0] // 2]  # middle frame
        if arr.ndim == 3:
            arr = arr[:, :, 0]
        arr = arr.astype(float)
        arr -= arr.min()
        mx = arr.max()
        if mx > 0:
            arr /= mx
        arr = (arr * 255).astype(np.uint8)
        img = Image.fromarray(arr, mode="L").convert("RGB")
        img.thumbnail((256, 256), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "DICOM Metadata Explorer API", "version": "2.0.0"}


@app.get("/dataset-info")
def dataset_info():
    """Catalog: data type, folder paths, how records are exposed via API."""
    return get_dataset_catalog()


@app.post("/sync-data")
def sync_data(force: bool = False):
    """Copy project Data/DICOM_samples → APP/data/DICOM_samples."""
    return sync_dicom_to_app(force=force)


@app.get("/plots")
def get_plots():
    """Matplotlib figures (base64 PNG) computed from the currently loaded cohort."""
    return generate_plot_bundle(_records)


@app.get("/data-tree")
def data_tree():
    """Filesystem view: folders, files, extensions (APP mirror + project source)."""
    loaded = {r["filename"] for r in _records}
    return {
        **get_data_tree(loaded),
        "cohort_loaded": len(_records),
        "active_folder": display_path(_loaded_folder) if _loaded_folder else None,
        "auto_loaded_on_startup": _auto_loaded,
    }


@app.get("/bootstrap")
def bootstrap():
    """Initial UI payload: tree + ingestion status + record count."""
    loaded = {r["filename"] for r in _records}
    return {
        "auto_loaded": _auto_loaded,
        "active_folder": display_path(_loaded_folder) if _loaded_folder else None,
        "cohort_size": len(_records),
        "ingest": {
            "loaded": len(_records),
            "folder": display_path(_loaded_folder) if _loaded_folder else None,
        },
        "data_tree": get_data_tree(loaded),
    }


@app.post("/upload")
async def upload_dicoms(files: List[UploadFile] = File(...)):
    """Upload one or more DICOM files and extract metadata."""
    results = []
    errors = []

    for upload in files:
        try:
            contents = await upload.read()
            suffix = os.path.splitext(upload.filename)[-1] or ".dcm"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(contents)
                tmp_path = tmp.name

            record_id = f"rec_{len(_records) + len(results):04d}"
            meta = _extract_metadata(tmp_path, record_id)
            thumbnail = _generate_thumbnail(tmp_path)

            _records.append(meta)
            if thumbnail:
                _images[record_id] = thumbnail

            os.unlink(tmp_path)
            results.append({"status": "ok", "id": record_id, "filename": upload.filename})
        except Exception as e:
            errors.append({"filename": upload.filename, "error": str(e)})

    return {
        "uploaded": len(results),
        "failed": len(errors),
        "records": results,
        "errors": errors,
    }


@app.get("/records")
def get_records():
    """Return all processed records."""
    return {"total": len(_records), "records": _records}


@app.get("/summary")
def get_summary():
    """Return aggregated statistics across all loaded DICOM files."""
    if not _records:
        return {"total": 0, "message": "No records loaded yet."}

    df = pd.DataFrame(_records)

    # Modality counts
    modality_counts = df["modality"].value_counts().to_dict()

    # Body part counts
    body_part_counts = df["body_part"].value_counts().to_dict()

    # Age stats
    ages = df["patient_age_years"].dropna()
    age_stats = {
        "count": int(ages.count()),
        "mean": round(float(ages.mean()), 1) if not ages.empty else None,
        "min": round(float(ages.min()), 1) if not ages.empty else None,
        "max": round(float(ages.max()), 1) if not ages.empty else None,
        "std": round(float(ages.std()), 1) if not ages.empty else None,
    }

    # Sex distribution
    sex_counts = df["patient_sex"].value_counts().to_dict()

    # Image size stats
    rows = df["rows"].dropna()
    cols = df["cols"].dropna()
    image_size_stats = {
        "mean_rows": round(float(rows.mean()), 1) if not rows.empty else None,
        "mean_cols": round(float(cols.mean()), 1) if not cols.empty else None,
        "max_rows": int(rows.max()) if not rows.empty else None,
        "max_cols": int(cols.max()) if not cols.empty else None,
    }

    # Bits allocated
    bits = df["bits_allocated"].dropna().value_counts().to_dict()
    bits = {str(k): int(v) for k, v in bits.items()}

    # Has pixel data
    has_px = int(df["has_pixel_data"].sum()) if "has_pixel_data" in df.columns else 0

    # Acquisition date distribution
    dates = df["acquisition_date"].dropna()
    dates = dates[dates != "N/A"]
    date_year_counts = {}
    for d in dates:
        try:
            year = str(d)[:4]
            date_year_counts[year] = date_year_counts.get(year, 0) + 1
        except Exception:
            pass

    return {
        "total": len(_records),
        "modality_counts": modality_counts,
        "body_part_counts": body_part_counts,
        "sex_counts": sex_counts,
        "age_stats": age_stats,
        "image_size_stats": image_size_stats,
        "bits_allocated_counts": bits,
        "has_pixel_data": has_px,
        "acquisition_year_counts": date_year_counts,
    }


@app.get("/image/{record_id}")
def get_image(record_id: str):
    """Return base64 PNG thumbnail for a record, if available."""
    if record_id not in _images:
        raise HTTPException(status_code=404, detail="No image available for this record.")
    return {"record_id": record_id, "thumbnail_b64": _images[record_id]}


@app.post("/scan-folder")
def scan_folder(folder_path: Optional[str] = None, reset: bool = True):
    """Reload DICOM corpus from disk (default: APP/data/DICOM_samples)."""
    if not folder_path:
        folder_path = default_scan_folder()
    return _ingest_folder(folder_path, reset=reset)


@app.delete("/clear")
def clear_records():
    """Wipe cohort (UI can trigger reload via POST /scan-folder)."""
    global _loaded_folder, _auto_loaded
    _records.clear()
    _images.clear()
    _loaded_folder = None
    _auto_loaded = False
    return {"message": "All records cleared."}
