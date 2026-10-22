"""Thin client for the WasteWise FastAPI backend. No Streamlit code in here."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

TIMEOUT_HEALTH = 4
TIMEOUT_DETECT = 120  # first CPU request can be slow


class ApiError(Exception):
    """A problem we can show to the user as-is."""


@dataclass
class Health:
    online: bool
    model_loaded: bool = False
    model_name: Optional[str] = None
    class_names: Optional[Dict[str, str]] = None
    detail: Optional[str] = None


def get_health(base_url: str) -> Health:
    base = base_url.rstrip("/")
    try:
        r = requests.get(f"{base}/api/v1/health", timeout=TIMEOUT_HEALTH)
        r.raise_for_status()
        d = r.json()
    except requests.RequestException as err:
        return Health(online=False, detail=f"Cannot reach the API at {base} ({type(err).__name__}).")
    except ValueError:
        return Health(online=False, detail="The API answered, but not with valid JSON.")
    return Health(
        online=True,
        model_loaded=bool(d.get("model_loaded")),
        model_name=d.get("model_name"),
        class_names=d.get("class_names"),
        detail=d.get("detail"),
    )


def detect(base_url: str, data: bytes, filename: str, content_type: str,
           confidence: float, iou: float) -> Dict[str, Any]:
    """Call POST /api/v1/detect. Always asks for the annotated image."""
    base = base_url.rstrip("/")
    params = {"confidence": confidence, "iou": iou, "return_image": "true"}
    files = {"file": (filename or "image.jpg", data, content_type or "image/jpeg")}
    try:
        r = requests.post(f"{base}/api/v1/detect", params=params, files=files, timeout=TIMEOUT_DETECT)
    except requests.ConnectionError:
        raise ApiError(f"Cannot connect to the backend at {base}. Is `uvicorn app.main:app` running?")
    except requests.Timeout:
        raise ApiError("The backend took too long to answer. Try a smaller image.")
    except requests.RequestException as err:
        raise ApiError(f"Request failed: {err}")

    if r.status_code != 200:
        try:
            detail = r.json().get("detail", r.text)
        except ValueError:
            detail = r.text[:200]
        if isinstance(detail, list):  # FastAPI 422 validation errors
            detail = "; ".join(str(x.get("msg", x)) for x in detail)
        raise ApiError(f"{detail} (HTTP {r.status_code})")
    try:
        return r.json()
    except ValueError:
        raise ApiError("The backend returned an unreadable response.")


def decode_annotated(result: Dict[str, Any]) -> Optional[bytes]:
    b64 = result.get("annotated_image_base64")
    return base64.b64decode(b64) if b64 else None
