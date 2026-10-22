"""WasteWise AI backend. Start with:  uvicorn app.main:app --reload"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("wastewise")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the model once when the server starts (not on every request)."""
    app.state.detector = None
    app.state.model_error = None
    try:
        from app.services.detector import Detector
        app.state.detector = Detector(get_settings())
    except Exception as err:                       # keep the server up so /health can explain the problem
        app.state.model_error = str(err)
        logger.error("Could not load the model: %s", err)
    yield


app = FastAPI(
    title="WasteWise AI",
    version="1.0.0",
    description="Detects Paper, Plastic Bottle, Plastic bag and Plastic waste in an image. "
                "Advisory only: a prediction does not prove an item is recyclable.",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/", include_in_schema=False)
def root():
    return {"service": "WasteWise AI", "docs": "/docs", "health": "/api/v1/health"}
