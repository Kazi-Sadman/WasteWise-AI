"""Tests for the API. A fake detector is used, so no model file or GPU is needed.

Run from the backend/ folder:   pytest
"""
import io
import json

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings, get_settings
from app.main import app
from app.services.detector import DetectionResult
from app.services.preprocessing import ImageValidationError, load_image
from app.services.waste_mapping import class_names_from_metadata, count_by_class

NAMES = {0: "Paper", 1: "Plastic Bottle", 2: "Plastic bag", 3: "Plastic waste"}


class FakeDetector:
    """Stands in for the real YOLO detector."""

    model_name = "fake detector"
    class_names = NAMES

    def __init__(self, found=True, fail=False):
        self.found, self.fail = found, fail

    def detect(self, image, confidence, iou, draw=False):
        if self.fail:
            raise RuntimeError("boom")
        width, height = image.size
        detections = []
        if self.found:
            detections = [{"class_id": 1, "class_name": "Plastic Bottle", "confidence": 0.93,
                           "bbox": {"x_min": 1.0, "y_min": 2.0, "x_max": 30.0, "y_max": 40.0}}]
        return DetectionResult(width, height, detections, count_by_class([d["class_id"] for d in detections], NAMES),
                               1.5, b"\xff\xd8fakejpeg" if draw else None)


def make_image_bytes(fmt="PNG", size=(64, 48)):
    buffer = io.BytesIO()
    Image.new("RGB", size, (120, 200, 80)).save(buffer, format=fmt)
    return buffer.getvalue()


@pytest.fixture
def client():
    app.state.detector = FakeDetector()
    app.state.model_error = None
    app.dependency_overrides[get_settings] = lambda: Settings(max_upload_mb=1)
    yield TestClient(app)
    app.dependency_overrides.clear()


def post(client, content, content_type="image/png", name="a.png", **params):
    return client.post("/api/v1/detect", files={"file": (name, content, content_type)}, params=params)


# ---------------- endpoint tests ----------------
def test_health_ok(client):
    body = client.get("/api/v1/health").json()
    assert body["status"] == "ok" and body["model_loaded"] is True
    assert body["class_names"]["0"] == "Paper"


def test_detect_valid_image(client):
    response = post(client, make_image_bytes())
    assert response.status_code == 200
    body = response.json()
    assert body["image_width"] == 64 and body["image_height"] == 48
    assert body["detections"][0]["class_name"] == "Plastic Bottle"
    assert body["counts_by_class"] == {"Paper": 0, "Plastic Bottle": 1, "Plastic bag": 0, "Plastic waste": 0}
    assert body["annotated_image_base64"] is None


def test_detect_jpeg_and_return_image(client):
    response = post(client, make_image_bytes("JPEG"), "image/jpeg", "a.jpg", return_image="true")
    assert response.status_code == 200
    assert response.json()["annotated_image_base64"]


def test_no_detections_returns_empty_list_not_error(client):
    app.state.detector = FakeDetector(found=False)
    body = post(client, make_image_bytes()).json()
    assert body["detections"] == []
    assert set(body["counts_by_class"].values()) == {0}


def test_wrong_content_type_is_415(client):
    assert post(client, b"hello", "text/plain", "a.txt").status_code == 415


def test_corrupt_image_is_400(client):
    assert post(client, b"this is not an image at all").status_code == 400


def test_truncated_image_is_400(client):
    assert post(client, make_image_bytes("PNG")[:40]).status_code == 400


def test_empty_file_is_400(client):
    assert post(client, b"").status_code == 400


def test_too_large_is_413(client):
    assert post(client, b"0" * (1024 * 1024 + 10)).status_code == 413


def test_missing_file_is_422(client):
    assert client.post("/api/v1/detect").status_code == 422


def test_confidence_out_of_range_is_422(client):
    assert post(client, make_image_bytes(), confidence=1.5).status_code == 422


def test_model_failure_is_500(client):
    app.state.detector = FakeDetector(fail=True)
    assert post(client, make_image_bytes()).status_code == 500


def test_model_not_loaded_is_503(client):
    app.state.detector = None
    app.state.model_error = "missing best.pt"
    assert post(client, make_image_bytes()).status_code == 503
    health = client.get("/api/v1/health").json()
    assert health["status"] == "degraded" and health["model_loaded"] is False


# ---------------- unit tests ----------------
def test_load_image_converts_to_rgb():
    image = load_image(make_image_bytes(), "image/png", 10**6, 10**6)
    assert image.mode == "RGB"


def test_load_image_rejects_huge_pixel_count():
    with pytest.raises(ImageValidationError) as err:
        load_image(make_image_bytes(size=(100, 100)), "image/png", 10**6, 50)
    assert err.value.status_code == 413


def test_count_by_class_includes_zero_counts():
    assert count_by_class([0, 0, 3], NAMES) == {"Paper": 2, "Plastic Bottle": 0, "Plastic bag": 0, "Plastic waste": 1}


def test_class_names_prefer_metadata_and_fall_back_to_model(tmp_path):
    metadata = tmp_path / "meta.json"
    metadata.write_text(json.dumps({"class_names": {str(k): v for k, v in NAMES.items()}}))
    assert class_names_from_metadata(metadata, NAMES) == NAMES
    # metadata that disagrees with the model -> trust the model
    metadata.write_text(json.dumps({"class_names": {"0": "Glass"}}))
    assert class_names_from_metadata(metadata, NAMES) == NAMES
    # no metadata file at all -> model names
    assert class_names_from_metadata(tmp_path / "missing.json", NAMES) == NAMES
