# DICOM Metadata Explorer

PGE5 — web app to explore DICOM metadata across a multi-modality teaching corpus.

## Run

**Backend** (from repo root):

```bash
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000
```

**Frontend** (second terminal):

```bash
cd frontend && npm install && npm run dev
```

Open http://localhost:5173 — the bundled DICOM folder (`data/DICOM_samples`) loads automatically.

## Stack

- Python FastAPI + pydicom (backend)
- React + TypeScript + Vite (frontend)

## Data

`data/DICOM_samples/` contains the pydicom test DICOM corpus (78 `.dcm` files), mirrored from the course project `Data/DICOM_samples`.
