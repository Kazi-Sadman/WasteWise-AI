"""Request/response shapes for the API (validated by Pydantic)."""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Pixel coordinates in the ORIGINAL uploaded image. Origin is the top-left corner."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float


class Detection(BaseModel):
    class_id: int
    class_name: str
    confidence: float = Field(ge=0, le=1)
    bbox: BoundingBox


class DetectionResponse(BaseModel):
    model_name: str
    image_width: int
    image_height: int
    confidence_threshold: float
    detections: List[Detection]
    counts_by_class: Dict[str, int]
    inference_ms: float
    annotated_image_base64: Optional[str] = Field(
        default=None, description="JPEG with boxes drawn, base64 encoded. Only when return_image=true."
    )


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: Optional[str] = None
    class_names: Optional[Dict[str, str]] = None
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str
