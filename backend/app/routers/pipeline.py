import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.database import async_session
from app.models.camera import Camera
from app.pipeline.camera_pipeline import CameraPipelineConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])


@router.get("/status")
async def get_pipeline_status(request: Request) -> dict[str, Any]:
    """Get the status of all active camera pipelines."""
    manager = request.app.state.pipeline_manager
    return manager.get_status()


@router.post("/cameras/{camera_id}/start")
async def start_camera_pipeline(camera_id: str, request: Request) -> dict[str, str]:
    """Start the detection pipeline for a specific camera."""
    manager = request.app.state.pipeline_manager

    # Look up the camera in the database
    try:
        cam_uuid = uuid.UUID(camera_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid camera ID format") from exc

    async with async_session() as session:
        result = await session.execute(select(Camera).where(Camera.id == cam_uuid))
        camera = result.scalar_one_or_none()

    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")

    if not camera.is_enabled:
        raise HTTPException(status_code=400, detail="Camera is disabled")

    config = CameraPipelineConfig(
        camera_id=str(camera.id),
        camera_name=camera.name,
        rtsp_url=camera.rtsp_url_encrypted,  # In production, decrypt first
        sub_stream_url=camera.sub_stream_url_encrypted,
    )

    await manager.add_camera(config)
    return {"status": "started", "camera_id": camera_id}


@router.post("/cameras/{camera_id}/stop")
async def stop_camera_pipeline(camera_id: str, request: Request) -> dict[str, str]:
    """Stop the detection pipeline for a specific camera."""
    manager = request.app.state.pipeline_manager
    await manager.remove_camera(camera_id)
    return {"status": "stopped", "camera_id": camera_id}
