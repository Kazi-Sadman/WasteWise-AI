# WasteWise AI

Detects waste in a photo — **Paper, Plastic Bottle, Plastic bag, Plastic waste** — and returns a box, class name and confidence for every object, plus counts per class.

- **Training:** one Google Colab notebook (Ultralytics YOLO11n, transfer learning).
- **Serving:** a FastAPI backend that loads the trained model once and exposes `POST /api/v1/detect`.
- **Frontend:** Streamlit, planned for later.

> WasteWise AI is advisory. It does not sort waste, and a prediction does not prove an item is recyclable where you live.

## ⚠️ Read first: re-run training before quoting metrics

The first Colab run mixed two overlapping dataset partitions and its audit could not read polygon labels. The model file works for the backend, but the numbers in `reports/` from that run are optimistic and the error-analysis section is invalid. Apply [`docs/notebook_fixes.md`](docs/notebook_fixes.md), retrain, and replace the reports and `best.pt`.

## Project layout

```
WasteWise-AI/
├── notebooks/WasteWise_AI_Colab_Training.ipynb   ← your trained notebook (put it here)
├── backend/
│   ├── app/
│   │   ├── main.py                 app + model loaded once at startup
│   │   ├── config.py               settings from .env
│   │   ├── api/routes.py           /health and /detect
│   │   ├── schemas/detection.py    response models
│   │   └── services/
│   │       ├── detector.py         YOLO wrapper
│   │       ├── preprocessing.py    upload checks + decoding
│   │       └── waste_mapping.py    class names + counts
│   ├── models/                     ← put best.pt and model_metadata.json here
│   ├── tests/test_detection.py
│   ├── requirements.txt
│   └── .env.example
├── reports/                        ← put dataset_audit.json, evaluation.json, evaluation.md here
├── docs/{project_design.md, notebook_fixes.md}
├── .gitignore
└── README.md
```

Copy your existing files into place (they are not included here): `best.pt` and `model_metadata.json` → `backend/models/`; notebook → `notebooks/`; reports → `reports/`.

## Run the backend

Python 3.10+ is recommended.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt      # installs PyTorch via ultralytics (large download)
cp .env.example .env                 # optional: change thresholds, DEVICE, limits
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive Swagger page. Check http://127.0.0.1:8000/api/v1/health — it should say `"model_loaded": true` and list the four classes. If `best.pt` is missing the server still starts, `/health` explains why and `/detect` returns 503.

### Try it

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/detect?confidence=0.25" \
     -F "file=@my_photo.jpg"
```

Add `&return_image=true` to also get the annotated picture as base64 JPEG in `annotated_image_base64`.

```json
{
  "model_name": "WasteWise YOLO detector (yolo11n.pt)",
  "image_width": 1280,
  "image_height": 720,
  "confidence_threshold": 0.25,
  "detections": [
    {"class_id": 1, "class_name": "Plastic Bottle", "confidence": 0.93,
     "bbox": {"x_min": 40, "y_min": 35, "x_max": 180, "y_max": 260}}
  ],
  "counts_by_class": {"Paper": 0, "Plastic Bottle": 1, "Plastic bag": 0, "Plastic waste": 0},
  "inference_ms": 85.2,
  "annotated_image_base64": null
}
```

(Illustrative example, not a real prediction.) Boxes are pixels in the original image, origin top-left.

| Status | Meaning |
|---|---|
| 200 | OK (an empty `detections` list means nothing was found — not an error) |
| 400 | Empty, corrupt or unreadable image |
| 413 | File larger than `MAX_UPLOAD_MB` or too many pixels |
| 415 | Not JPEG/PNG/WEBP/BMP |
| 422 | Bad parameter (e.g. `confidence=1.5`) |
| 500 | Model failed while running |
| 503 | Model not loaded |

## Configuration (`backend/.env`)

| Variable | Default | Meaning |
|---|---|---|
| `MODEL_PATH` | `models/best.pt` | Relative to `backend/` |
| `METADATA_PATH` | `models/model_metadata.json` | Class names, checksum |
| `CONFIDENCE_THRESHOLD` | `0.25` | Default minimum confidence |
| `IOU_THRESHOLD` | `0.7` | Default NMS overlap |
| `IMAGE_SIZE` | `640` | Must match training size |
| `MAX_UPLOAD_MB` | `10` | Upload limit |
| `DEVICE` | `cpu` | `cpu` or a GPU index like `0` |

## Tests

```bash
cd backend
pytest
```

The tests use a fake detector, so they need no model or GPU: valid image, no detections, wrong type, corrupt/truncated/empty file, oversized file, bad parameters, model failure and model-not-loaded.

Real-model smoke test (needs `best.pt` in `backend/models/`):

```bash
cd backend
python - <<'PY'
from ultralytics import YOLO
m = YOLO("models/best.pt")
r = m.predict("some_photo.jpg", conf=0.25, device="cpu", verbose=False)[0]
print(m.names, len(r.boxes), "detections")
PY
```

Verify the model file: `sha256sum models/best.pt` should equal the `sha256` in `model_metadata.json` (the server also warns at startup if it doesn't).

## Design notes

- The model is loaded **once** at startup, not per request; one prediction runs at a time.
- Uploads are validated (size, type, decode) and are **never written to disk**.
- Class names come from the model/metadata, not hard-coded, so retraining with a different class order cannot silently mislabel results.
- No CORS is enabled: a Streamlit app calls the API from its own server. Add CORS only if a browser page will call it directly.

## Dataset and licenses

Data: *A Curated Recyclable Waste Object Detection Dataset from Public Spaces in Southeastern Bangladesh*, Mazumder, S. H., Zenodo, DOI 10.5281/zenodo.22043339, **CC BY 4.0** — credit the authors. Check Ultralytics' current license terms before commercial use. Neither is legal advice from this project.

## Limitations

Only four classes; small, occluded, dirty or overlapping objects may be missed; "Plastic waste" was the weakest class in the first run; images come from one region; confidence is not a guarantee.
