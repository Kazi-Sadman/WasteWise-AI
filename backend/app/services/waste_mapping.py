"""Class-name handling: which id means which waste type, and per-class counts."""
import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List

logger = logging.getLogger("wastewise")


def class_names_from_metadata(metadata_path: Path, model_names: Dict[int, str]) -> Dict[int, str]:
    """Return {class_id: name}.

    The names saved next to the model (model_metadata.json) are preferred. If they
    disagree with the names stored inside best.pt we trust the model file and warn.
    """
    model_names = {int(k): str(v) for k, v in model_names.items()}
    if not metadata_path.exists():
        logger.warning("Metadata file %s not found - using names stored inside the model.", metadata_path)
        return model_names

    metadata = json.loads(metadata_path.read_text())
    from_metadata = {int(k): str(v) for k, v in metadata.get("class_names", {}).items()}
    if from_metadata and from_metadata != model_names:
        logger.warning("Class names in metadata differ from the model (%s vs %s). Using the model's.",
                       from_metadata, model_names)
        return model_names
    return from_metadata or model_names


def count_by_class(class_ids: Iterable[int], names: Dict[int, str]) -> Dict[str, int]:
    """Count detections per class. Every known class appears, with 0 if not found."""
    counts: Dict[str, int] = {names[i]: 0 for i in sorted(names)}
    for class_id in class_ids:
        counts[names[class_id]] += 1
    return counts


def ordered_names(names: Dict[int, str]) -> List[str]:
    return [names[i] for i in sorted(names)]
