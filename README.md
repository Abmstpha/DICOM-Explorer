# DICOM Metadata Explorer

A web application to browse, summarize, and visualize **DICOM** metadata across a multi-modality imaging corpus (CT, MRI, ultrasound, nuclear medicine, radiotherapy, and more).

Load a folder of `.dcm` files and get cohort statistics, distribution charts, a searchable metadata table, and image previews when pixel data are available.

## Features

- Automatic ingestion of a bundled sample corpus on startup
- Summary statistics: modality, patient demographics, acquisition dates, image dimensions
- Charts: modality, body region, sex, age, bit depth, pixel availability
- Instance-level registry with DICOM field extraction
- Optional reload from disk or reset cohort

## Quick start

**Requirements:** Python 3.9+, Node.js 18+

**1. Backend** (from repository root):

```bash
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000
```

**2. Frontend** (second terminal):

```bash
cd frontend && npm install && npm run dev
```

**3. Open** [http://localhost:5173](http://localhost:5173)

The sample dataset in `data/DICOM_samples/` (78 public pydicom test files) is loaded automatically.

## Project structure

```
backend/          FastAPI service (metadata extraction, plots, file index)
frontend/         React + TypeScript UI
data/DICOM_samples/   Sample DICOM corpus (.dcm)
```

## Extracted metadata

| Field | DICOM context |
|-------|----------------|
| Modality | Imaging type (CT, MR, US, …) |
| Patient age | From Patient Age tag |
| Acquisition date | Acquisition or study date |
| Body part examined | Anatomical region |
| Patient sex | Demographics |
| Image size | Rows × columns when present |

## Tech stack

- **Backend:** Python, FastAPI, pydicom, pandas, matplotlib
- **Frontend:** React, TypeScript, Vite

## Sample data

`data/DICOM_samples/` ships with the [pydicom test dataset](https://github.com/pydicom/pydicom/tree/main/src/pydicom/data/test_files) — real DICOM files intended for library testing, suitable for demonstrating metadata workflows without clinical PHI.

Replace or extend this folder with your own `.dcm` collection and use **Reload corpus from disk** in the UI.

## Git hooks (optional)

To keep commits single-author only:

```bash
cp .githooks/commit-msg .git/hooks/commit-msg && chmod +x .git/hooks/commit-msg
```

## License

Use and adapt for learning, research, and prototyping. Sample DICOM files remain subject to their original pydicom test-data terms.
