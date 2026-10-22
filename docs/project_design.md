# WasteWise AI — Project Design

Version 1.1 · Computer vision / object detection · Colab training · FastAPI backend · Streamlit UI (later)

## 1. Summary

WasteWise AI detects waste objects in one image. For each object it returns a bounding box, a class name and a confidence score, and it counts detections per class. It is an **advisory** tool: it does not sort waste, and a prediction does not prove an item is recyclable under local rules.

## 2. Scope

| Part | Status |
|---|---|
| Model training in one Colab notebook (`notebooks/`) | Done once; **must be re-run** after the fixes in `docs/notebook_fixes.md` |
| FastAPI backend (`backend/`) | Implemented, unit-tested with a fake detector |
| Streamlit frontend | Not started (planned) |

## 3. Dataset (what the archive actually contains)

Source: *A Curated Recyclable Waste Object Detection Dataset from Public Spaces in Southeastern Bangladesh*, Zenodo record 22043339, DOI 10.5281/zenodo.22043339, license **CC BY 4.0**.

- 2,842 images, 6,076 object instances, YOLO-format labels.
- The archive holds **two alternative partitions of the same images**: `data_canonical_75-15-10` and `data_robustness_70-15-15`. Use **one** partition, not both (see §7).
- Class order from the dataset's own `data.yaml`: `0 Paper`, `1 Plastic Bottle`, `2 Plastic bag`, `3 Plastic waste`. (This differs from the order guessed in the first design draft; the backend reads names from the model, so it is unaffected.)
- Label files contain polygon points (many numbers per line), not only 5-number boxes. Ultralytics converts them to boxes for training; custom code must do the same.

## 4. Architecture

```
Training (Colab)                         Serving (local)
dataset → audit → train YOLO11n    →     best.pt + model_metadata.json
        → evaluate → export                    │
                                               ▼
client ──► POST /api/v1/detect ──► validate upload ──► decode (RGB, EXIF-rotate)
                                               │
                                     YOLO (loaded once at startup)
                                               │
                         detections + counts_by_class (+ optional annotated image)
```

Backend modules:

| File | Job |
|---|---|
| `app/config.py` | Settings from `.env`; paths resolved from `backend/` |
| `app/main.py` | Creates the app, loads the model once at startup, keeps the server up if the model is missing (503 + `/health` explains) |
| `app/api/routes.py` | `GET /api/v1/health`, `POST /api/v1/detect` |
| `app/schemas/detection.py` | Response/validation models |
| `app/services/preprocessing.py` | Size, type, pixel-count and decode checks |
| `app/services/detector.py` | YOLO wrapper, checksum check, box clipping, optional drawing |
| `app/services/waste_mapping.py` | Class-id → name, per-class counts (zeros included) |

## 5. API contract

`POST /api/v1/detect` — multipart form field `file`; query params `confidence` (0–1), `iou` (0–1), `return_image` (bool).

```json
{
  "model_name": "WasteWise YOLO detector (yolo11n.pt)",
  "image_width": 1280, "image_height": 720,
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

Boxes are **pixels in the original uploaded image**, origin top-left, `[x_min, y_min, x_max, y_max]`. This example is illustrative, not a real prediction.

Errors: 400 empty/corrupt image · 413 too large · 415 wrong file type · 422 bad parameter · 500 model failure · 503 model not loaded.

## 6. Evaluation status

Metrics are object-detection metrics (mAP50, mAP50-95, precision, recall) from Ultralytics. The first training run produced numbers (e.g. test mAP50 ≈ 0.72), **but they must not be quoted yet**: that run mixed both partitions (§7). Re-run with one partition and use the new `reports/evaluation.*`.

Also, the "error analysis" block in the first `evaluation.md` (4 correct / 2950 false positives) is **invalid**: it was computed from labels the notebook failed to parse (polygons). It does not describe the model.

## 7. Known issues and decisions

1. **Partition mixing / leakage.** The first run trained on the `train` folders of both partitions and tested on both `test` folders. Because both partitions are different splits of the same photos, 143 identical images appear in different splits, so test scores are optimistic. Fix: train and evaluate on `data_canonical_75-15-10` only.
2. **Polygon labels** were rejected by the audit parser (12,142 "malformed" lines) so the label-drawing check and the error analysis were wrong. Fix: parse polygons into boxes.
3. `best.pt` currently in use works for the backend demo (its SHA-256 matches `model_metadata.json`), but should be replaced after retraining.

## 8. Risks and limitations

- Four classes only; other objects can be missed or mislabelled.
- Small, occluded, dirty, blurred or overlapping objects may be missed; "Plastic waste" is the weakest class in the first run.
- Images come from one region; accuracy elsewhere is unknown.
- Confidence is not a guarantee. Recyclability depends on local facilities.
- Check Ultralytics' current license (AGPL-3.0 / enterprise) before commercial use. The dataset is CC BY 4.0: credit the authors.

## 9. Phases

1. ✅ Dataset verification and first training run
2. ⚠️ Fix notebook (one partition, polygon parser), retrain, regenerate reports
3. ✅ Backend implemented and tested
4. ⏳ Run the real-model smoke test with the retrained `best.pt`
5. ⏳ Streamlit frontend that calls `/api/v1/detect`
