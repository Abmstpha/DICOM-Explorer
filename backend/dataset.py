"""Dataset paths, sync from project Data/, and catalog metadata."""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# APP/backend/dataset.py → project root is ../../ 
BACKEND_DIR = Path(__file__).resolve().parent
APP_DIR = BACKEND_DIR.parent
PROJECT_ROOT = APP_DIR.parent

SOURCE_DICOM = PROJECT_ROOT / "Data" / "DICOM_samples"
APP_DICOM = APP_DIR / "data" / "DICOM_samples"
APP_DATA_ROOT = APP_DIR / "data"

# Recognised on-disk patterns for DICOM ingestion
DICOM_EXTENSIONS = {".dcm", ".dicom", ".dicomdir"}


def display_path(path: str | Path) -> str:
    """Project-relative path for UI/API (never expose absolute home paths)."""
    p = Path(path).resolve()
    try:
        return p.relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return Path(path).name


def sync_dicom_to_app(force: bool = False) -> Dict[str, Any]:
    """Copy DICOM test files into APP/data/DICOM_samples for self-contained demo."""
    if not SOURCE_DICOM.is_dir():
        return {"ok": False, "error": f"Source missing: {display_path(SOURCE_DICOM)}"}

    APP_DICOM.mkdir(parents=True, exist_ok=True)
    src_files = sorted(SOURCE_DICOM.glob("*.dcm"))
    if not src_files:
        return {"ok": False, "error": "No .dcm files in source folder"}

    dest_count = len(list(APP_DICOM.glob("*.dcm")))
    if not force and dest_count >= len(src_files):
        return {
            "ok": True,
            "action": "skipped",
            "source": display_path(SOURCE_DICOM),
            "destination": display_path(APP_DICOM),
            "file_count": dest_count,
        }

    copied = 0
    for src in src_files:
        dest = APP_DICOM / src.name
        if force or not dest.exists():
            shutil.copy2(src, dest)
            copied += 1

    return {
        "ok": True,
        "action": "copied",
        "source": display_path(SOURCE_DICOM),
        "destination": display_path(APP_DICOM),
        "file_count": len(list(APP_DICOM.glob("*.dcm"))),
        "copied": copied,
    }


def default_scan_folder() -> str:
    """Prefer APP-local copy, then project Data/."""
    sync_dicom_to_app(force=False)
    if APP_DICOM.is_dir() and any(APP_DICOM.glob("*.dcm")):
        return str(APP_DICOM)
    return str(SOURCE_DICOM)


def classify_extension(filename: str) -> Dict[str, str]:
    """Return display labels for file extension."""
    _, ext = os.path.splitext(filename.lower())
    if ext == ".dicomdir":
        fmt, display = "DICOMDIR index", ".dicomdir"
    elif ext in DICOM_EXTENSIONS:
        fmt, display = "DICOM Part 10", ext
    elif ext == "":
        fmt, display = "No extension", "(none)"
    else:
        fmt, display = f"{ext.lstrip('.').upper()} file", ext
    return {
        "extension": display,
        "extension_normalized": ext if ext in DICOM_EXTENSIONS else (ext or "none"),
        "format_label": fmt,
    }


def iter_dicom_paths(folder: Path) -> List[Path]:
    """All ingestible DICOM paths under folder (by extension, then extensionless candidates)."""
    if not folder.is_dir():
        return []
    by_ext: List[Path] = []
    for p in sorted(folder.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() in DICOM_EXTENSIONS:
            by_ext.append(p)
    return by_ext


def list_folder_tree(
    folder: Path,
    tree_id: str,
    display_label: str,
    role: str,
    loaded_filenames: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    loaded_filenames = loaded_filenames or set()
    entries: List[Dict[str, Any]] = []
    ext_counts: Dict[str, int] = {}

    if folder.is_dir():
        for p in sorted(folder.iterdir()):
            if not p.is_file():
                continue
            info = classify_extension(p.name)
            ext_key = info["extension"]
            ext_counts[ext_key] = ext_counts.get(ext_key, 0) + 1
            entries.append(
                {
                    "type": "file",
                    "name": p.name,
                    "path": display_path(p),
                    "size_bytes": p.stat().st_size,
                    "extension": info["extension"],
                    "extension_normalized": info["extension_normalized"],
                    "format_label": info["format_label"],
                    "ingestible": p.suffix.lower() in DICOM_EXTENSIONS,
                    "loaded_in_cohort": p.name in loaded_filenames,
                }
            )

    return {
        "id": tree_id,
        "type": "folder",
        "label": display_label,
        "path": display_path(folder),
        "role": role,
        "file_count": len(entries),
        "extension_counts": ext_counts,
        "files": entries,
    }


def get_data_tree(loaded_filenames: Optional[Set[str]] = None) -> Dict[str, Any]:
    sync_dicom_to_app(force=False)
    loaded_filenames = loaded_filenames or set()
    roots = []
    for tree_id, path, label, role in [
        ("app_mirror", APP_DICOM, "APP/data/DICOM_samples (active corpus)", "active"),
        ("project_source", SOURCE_DICOM, "Data/DICOM_samples (project source)", "source"),
    ]:
        if path.is_dir():
            roots.append(list_folder_tree(path, tree_id, label, role, loaded_filenames))

    all_ext: Dict[str, int] = {}
    for r in roots:
        for k, v in r.get("extension_counts", {}).items():
            all_ext[k] = all_ext.get(k, 0) + v

    return {
        "app_data_root": display_path(APP_DATA_ROOT),
        "project_data_root": display_path(PROJECT_ROOT / "Data"),
        "roots": roots,
        "extension_summary": all_ext,
        "supported_ingest_extensions": sorted(DICOM_EXTENSIONS),
    }


def get_dataset_catalog() -> Dict[str, Any]:
    sync = sync_dicom_to_app(force=False)
    n_src = len(list(SOURCE_DICOM.glob("*.dcm"))) if SOURCE_DICOM.is_dir() else 0
    n_app = len(list(APP_DICOM.glob("*.dcm"))) if APP_DICOM.is_dir() else 0

    return {
        "title": "PGE5 Day 1 — DICOM Metadata Explorer (Task 2)",
        "data_type": "DICOM Part 10 files (.dcm)",
        "origin": "pydicom official test dataset (multi-modality teaching corpus)",
        "course_reference": "Same metadata workflow as OSIC / SIIM-COVID-19 / RSNA-style DICOM pipelines",
        "modalities_expected": ["CT", "MR", "US", "NM", "OT", "RTDOSE", "RTPLAN", "SR", "SEG", "ECG"],
        "paths": {
            "project_source": display_path(SOURCE_DICOM),
            "app_mirror": display_path(APP_DICOM),
            "project_data": display_path(PROJECT_ROOT / "Data"),
        },
        "file_counts": {"source_folder": n_src, "app_data_folder": n_app},
        "sync_status": sync,
        "fields_extracted": [
            "Modality",
            "Patient age",
            "Acquisition date",
            "Body part examined",
            "Patient sex",
            "Image dimensions",
        ],
        "what_you_see": [
            "Summary statistics across the loaded study files",
            "Charts by modality, body region, sex, and age",
            "Searchable table of every DICOM instance",
            "Preview images when pixel data are available",
        ],
    }
