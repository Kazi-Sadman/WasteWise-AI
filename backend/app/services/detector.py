"""Loads the YOLO model ONCE and runs detection on images."""
import base64
import hashlib
import io
import json
import logging
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from PIL import Image

from app.config import Settings
from app.services.waste_mapping import class_names_from_metadata, count_by_class

logger = logging.getLogger("wastewise")


@dataclass
class DetectionResult:
    width: int
    height: int
    detections: List[dict]            # plain dicts: class_id, class_name, confidence, bbox
    counts_by_class: Dict[str, int]
    inference_ms: float
    annotated_jpeg: Optional[bytes] = None


class Detector:
    def __init__(self, settings: Settings):
        # Imported here so the rest of the app (and the tests) work without ultralytics installed.
        from ultralytics import YOLO

        model_file = settings.model_file
        if not model_file.exists():
            raise FileNotFoundError(f"Model file not found: {model_file}. Copy best.pt into backend/models/.")

        self.settings = settings
        self.model = YOLO(str(model_file))
        self.class_names = class_names_from_metadata(settings.metadata_file, dict(self.model.names))
        self.model_name = self._read_model_name()
        self._lock = threading.Lock()          # one prediction at a time keeps memory use predictable
        self._check_checksum(model_file)
        logger.info("Model loaded: %s | classes: %s", model_file.name, self.class_names)

    # ---------- helpers ----------
    def _read_model_name(self) -> str:
        path = self.settings.metadata_file
        base = "yolo"
        if path.exists():
            base = json.loads(path.read_text()).get("base_model", base)
        return f"WasteWise YOLO detector ({base})"

    def _check_checksum(self, model_file) -> None:
        """Warn if best.pt is not the file the metadata describes."""
        path = self.settings.metadata_file
        if not path.exists():
            return
        expected = json.loads(path.read_text()).get("sha256")
        if not expected:
            return
        digest = hashlib.sha256(model_file.read_bytes()).hexdigest()
        if digest != expected:
            logger.warning("best.pt checksum does not match model_metadata.json - are these from the same run?")

    # ---------- public API ----------
    def detect(self, image: Image.Image, confidence: float, iou: float, draw: bool = False) -> DetectionResult:
        width, height = image.size
        started = time.perf_counter()

        logger.info(
            "Starting YOLO inference | image_size=%s | imgsz=%s | device=%s",
            image.size,
            self.settings.image_size,
            self.settings.device,
        )

        with self._lock:
            result = self.model.predict(
                image,
                conf=confidence,
                iou=iou,
                imgsz=self.settings.image_size,
                device=self.settings.device,
                verbose=False,
            )[0]

        elapsed_ms = (time.perf_counter() - started) * 1000

        logger.info(
            "YOLO inference completed in %.2f seconds",
            elapsed_ms / 1000,
        )

        detections = []
        class_ids = []
        for box, score, class_id in zip(result.boxes.xyxy.tolist(), result.boxes.conf.tolist(), result.boxes.cls.tolist()):
            class_id = int(class_id)
            x1, y1, x2, y2 = box
            detections.append({
                "class_id": class_id,
                "class_name": self.class_names[class_id],
                "confidence": round(float(score), 4),
                "bbox": {                                      # clipped to the image, in pixels
                    "x_min": round(max(0.0, x1), 1), "y_min": round(max(0.0, y1), 1),
                    "x_max": round(min(float(width), x2), 1), "y_max": round(min(float(height), y2), 1),
                },
            })
            class_ids.append(class_id)
        detections.sort(key=lambda d: -d["confidence"])

        jpeg = None
        if draw:
            annotated = Image.fromarray(result.plot()[..., ::-1])   # plot() returns BGR -> convert to RGB
            buffer = io.BytesIO()
            annotated.save(buffer, format="JPEG", quality=90)
            jpeg = buffer.getvalue()

        return DetectionResult(width, height, detections, count_by_class(class_ids, self.class_names),
                               round(elapsed_ms, 1), jpeg)


def jpeg_to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")
