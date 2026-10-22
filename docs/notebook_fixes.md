# Notebook fixes (apply, then retrain)

Your first run exposed two bugs in `WasteWise_AI_Colab_Training.ipynb`. Both were mine. The model file still works for the backend, but the **reports from that run should not be trusted** until you re-run with these fixes.

## What went wrong

| Symptom in your results | Cause |
|---|---|
| `train` had only 2 labelled objects, 12,142 "malformed" lines | Labels are polygons (e.g. 233 numbers per line). The audit parser only accepted 5-number boxes. |
| `annotation_samples.png` showed one tiny sliver box | Same parser problem, so the drawing step had almost no boxes. |
| Error analysis: 4 correct / 2,950 false positives | Ground truth came from the same broken parser. It says nothing about the model. |
| 2,842 duplicate image groups, 143 across splits, train + val + test counts ≈ 2× the dataset | The archive contains **two partitions of the same photos**. The notebook used both at once, so test images can also be in training. Test scores are too optimistic. |

The mAP / precision / recall numbers themselves come from Ultralytics (which understands polygons), but they were computed on the mixed data, so retrain and re-evaluate.

## Fix 1 — use one partition

Add this as a **new code cell right after Section 4** (the extraction cell):

```python
PARTITION = "data_canonical_75-15-10"          # use ONE partition only

if "EXTRACT_DIR" not in globals():
    EXTRACT_DIR = DATASET_DIR                  # remember the folder the archive was extracted into
matches = [p for p in EXTRACT_DIR.rglob(PARTITION) if p.is_dir()]
assert len(matches) == 1, f"Expected one folder named {PARTITION}, found {matches}"
DATASET_DIR = matches[0]                       # Sections 5-7 now only see this partition
print("Using partition:", DATASET_DIR)
```

## Fix 2 — accept polygon labels

In Section 6, replace the whole `parse_label_file` function with:

```python
def parse_label_file(path, n_classes):
    """Return (valid_boxes, problems). Accepts 5-number boxes AND polygon lines.

    Polygon lines (class x1 y1 x2 y2 x3 y3 ...) are converted to the tight box
    around their points, the same idea Ultralytics uses for detection training.
    """
    boxes, problems = [], []
    for line_no, line in enumerate(path.read_text(errors="replace").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        n_numbers = len(parts) - 1
        is_box = n_numbers == 4
        is_polygon = n_numbers >= 6 and n_numbers % 2 == 0
        if not (is_box or is_polygon):
            problems.append((line_no, "malformed_line", f"unexpected number of fields: {len(parts)}"))
            continue
        try:
            class_value = float(parts[0])
            numbers = [float(v) for v in parts[1:]]
        except ValueError:
            problems.append((line_no, "malformed_line", "non-numeric value"))
            continue
        if class_value != int(class_value) or not (0 <= class_value < n_classes):
            problems.append((line_no, "bad_class_id", f"class id {parts[0]} outside 0..{n_classes - 1}"))
            continue
        if not all(0.0 <= v <= 1.0 for v in numbers):
            problems.append((line_no, "bad_coordinates", "value outside 0..1 (labels may not be normalized)"))
            continue
        if is_box:
            xc, yc, w, h = numbers
        else:
            xs, ys = numbers[0::2], numbers[1::2]
            w, h = max(xs) - min(xs), max(ys) - min(ys)
            xc, yc = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        if w <= 0 or h <= 0:
            problems.append((line_no, "nonpositive_size", "width or height is zero/negative"))
            continue
        if xc - w / 2 < -1e-3 or yc - h / 2 < -1e-3 or xc + w / 2 > 1 + 1e-3 or yc + h / 2 > 1 + 1e-3:
            problems.append((line_no, "box_outside_image", "box extends past the image edge"))
        boxes.append((int(class_value), xc, yc, w, h))
    return boxes, problems
```

## Fix 3 (minor) — ignore README files when looking for labels

In Section 5, change the label test to:

```python
elif suffix == ".txt" and path.name.lower() not in DOC_TEXT_FILES and not path.name.lower().startswith("readme"):
```

This removes the 10 harmless "label_without_image" entries.

## Then re-run

1. In Section 2 set `RUN_NAME = "wastewise_yolo_v2"` and `FORCE_RETRAIN = True`.
2. Run Sections 2 → 14.
3. Sanity checks before trusting the results:
   - Section 6: `malformed_line` should be near 0, and the object count should be around 4,492 (train) / 1,048 (val) / 536 (test), matching the dataset README for the canonical partition.
   - Section 6: cross-split duplicate groups should be 0 (or very close).
   - Section 8: boxes should now sit on the objects, with several images shown.
   - Section 11: the error analysis should show a sensible number of correct detections.
4. Copy the new `best.pt`, `model_metadata.json`, `evaluation.*`, `dataset_audit.json` into `backend/models/` and `reports/`.
