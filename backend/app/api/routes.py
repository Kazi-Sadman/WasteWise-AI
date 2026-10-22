"""HTTP endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.config import Settings, get_settings
from app.schemas.detection import DetectionResponse, ErrorResponse, HealthResponse
from app.services.detector import jpeg_to_base64
from app.services.preprocessing import ImageValidationError, load_image

router = APIRouter(prefix="/api/v1")


def get_detector(request: Request):
    """Return the model loaded at startup, or a clear 503 if it could not be loaded."""
    detector = getattr(request.app.state, "detector", None)
    if detector is None:
        reason = getattr(request.app.state, "model_error", None) or "model not loaded"
        raise HTTPException(status_code=503, detail=f"Model is not available: {reason}")
    return detector


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(request: Request):
    detector = getattr(request.app.state, "detector", None)
    if detector is None:
        return HealthResponse(status="degraded", model_loaded=False,
                              detail=getattr(request.app.state, "model_error", None) or "model not loaded")
    return HealthResponse(status="ok", model_loaded=True, model_name=detector.model_name,
                          class_names={str(k): v for k, v in sorted(detector.class_names.items())})


@router.post(
    "/detect",
    response_model=DetectionResponse,
    tags=["detection"],
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse},
               415: {"model": ErrorResponse}, 500: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
async def detect(
    file: UploadFile = File(..., description="One image: JPEG, PNG, WEBP or BMP."),
    confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence (default from settings)."),
    iou: Optional[float] = Query(None, ge=0.0, le=1.0, description="NMS overlap threshold (default from settings)."),
    return_image: bool = Query(False, description="Also return the image with boxes drawn (base64 JPEG)."),
    detector=Depends(get_detector),
    settings: Settings = Depends(get_settings),
):
    # Read at most limit+1 bytes so a huge upload cannot fill memory.
    data = await file.read(settings.max_upload_bytes + 1)
    try:
        image = load_image(data, file.content_type, settings.max_upload_bytes, settings.max_image_pixels)
    except ImageValidationError as err:
        raise HTTPException(status_code=err.status_code, detail=err.message)

    conf = settings.confidence_threshold if confidence is None else confidence
    iou_value = settings.iou_threshold if iou is None else iou
    try:
        result = await run_in_threadpool(detector.detect, image, conf, iou_value, return_image)
    except Exception:
        raise HTTPException(status_code=500, detail="Detection failed while running the model.")

    return DetectionResponse(
        model_name=detector.model_name,
        image_width=result.width,
        image_height=result.height,
        confidence_threshold=conf,
        detections=result.detections,
        counts_by_class=result.counts_by_class,
        inference_ms=result.inference_ms,
        annotated_image_base64=jpeg_to_base64(result.annotated_jpeg) if result.annotated_jpeg else None,
    )
