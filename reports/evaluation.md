# WasteWise AI - Evaluation report

Model: `yolo11n.pt` fine-tuned; checkpoint `best.pt` from run `wastewise_yolo`.
Device used: Tesla T4. Class names source: dataset file: bangladesh_recyclable_waste_dataset/data_canonical_75-15-10/data.yaml.

## Validation split

precision 0.684 | recall 0.580 | mAP50 0.653 | mAP50-95 0.512

| class | precision | recall | mAP50 | mAP50-95 |
|---|---|---|---|---|
| Paper | 0.720 | 0.549 | 0.652 | 0.541 |
| Plastic Bottle | 0.785 | 0.707 | 0.786 | 0.653 |
| Plastic bag | 0.609 | 0.591 | 0.632 | 0.482 |
| Plastic waste | 0.622 | 0.471 | 0.539 | 0.374 |

## Test split

precision 0.758 | recall 0.648 | mAP50 0.724 | mAP50-95 0.588

| class | precision | recall | mAP50 | mAP50-95 |
|---|---|---|---|---|
| Paper | 0.800 | 0.686 | 0.789 | 0.680 |
| Plastic Bottle | 0.902 | 0.778 | 0.861 | 0.727 |
| Plastic bag | 0.762 | 0.696 | 0.762 | 0.579 |
| Plastic waste | 0.566 | 0.432 | 0.486 | 0.364 |

## Error analysis

Split `test`, confidence >= 0.25, IoU >= 0.5: 4 correct, 2950 false positives, 4 missed objects.

## Notes

- Validation numbers guided checkpoint choice; test numbers are the final estimate.
- Only four classes are supported; other objects may be missed or mislabelled.
- Per-image averages (ms) reported by the Ultralytics validator over the whole split, on this Colab machine at the configured batch size. Not representative of a local CPU.