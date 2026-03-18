import asyncio
import logging
from typing import Any

from app.pipeline.camera_pipeline import CameraPipeline, CameraPipelineConfig
from app.pipeline.detector.yolo_detector import DetectorConfig, YOLODetector
from app.pipeline.event_consumer import EventConsumer

logger = logging.getLogger(__name__)


class PipelineManager:
    """Manages all camera pipelines and the event consumer."""

    def __init__(self, detector_config: DetectorConfig | None = None) -> None:
        self._detector = YOLODetector(detector_config or DetectorConfig())
        self._pipelines: dict[str, CameraPipeline] = {}  # camera_id -> pipeline
        self._tasks: dict[str, asyncio.Task] = {}
        self._consumer = EventConsumer()
        self._consumer_task: asyncio.Task | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the shared detector model."""
        await asyncio.to_thread(self._detector.load)
        self._initialized = True
        logger.info("Pipeline manager initialized")

    async def start_consumer(self) -> None:
        """Start the event consumer."""
        self._consumer_task = asyncio.create_task(self._consumer.start())
        logger.info("Event consumer task started")

    async def add_camera(self, config: CameraPipelineConfig) -> None:
        """Add and start a camera pipeline."""
        if not self._initialized:
            raise RuntimeError(
                "Pipeline manager not initialized. Call initialize() first."
            )

        if config.camera_id in self._pipelines:
            logger.warning("Camera %s already has an active pipeline", config.camera_id)
            return

        pipeline = CameraPipeline(config=config, detector=self._detector)
        self._pipelines[config.camera_id] = pipeline
        self._tasks[config.camera_id] = asyncio.create_task(
            self._run_pipeline(config.camera_id, pipeline)
        )
        logger.info(
            "Camera pipeline added: %s (%s)", config.camera_id, config.camera_name
        )

    async def _run_pipeline(
        self, camera_id: str, pipeline: CameraPipeline
    ) -> None:
        """Run a camera pipeline with error handling."""
        try:
            await pipeline.start()
        except asyncio.CancelledError:
            logger.info("Pipeline cancelled for camera %s", camera_id)
        except Exception as e:
            logger.error("Pipeline error for camera %s: %s", camera_id, e)
        finally:
            await pipeline.stop()

    async def remove_camera(self, camera_id: str) -> None:
        """Stop and remove a camera pipeline."""
        if camera_id in self._tasks:
            self._tasks[camera_id].cancel()
            try:
                await self._tasks[camera_id]
            except asyncio.CancelledError:
                pass
            del self._tasks[camera_id]

        if camera_id in self._pipelines:
            del self._pipelines[camera_id]

        logger.info("Camera pipeline removed: %s", camera_id)

    async def shutdown(self) -> None:
        """Gracefully shut down all pipelines and the consumer."""
        logger.info("Shutting down pipeline manager...")

        # Stop all camera pipelines
        for camera_id in list(self._tasks.keys()):
            await self.remove_camera(camera_id)

        # Stop consumer
        if self._consumer_task:
            await self._consumer.stop()
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass

        logger.info("Pipeline manager shut down")

    def get_status(self) -> dict[str, Any]:
        """Get status of all pipelines."""
        return {
            "initialized": self._initialized,
            "active_cameras": len(self._pipelines),
            "cameras": {
                cid: {
                    "name": p.config.camera_name,
                    "fps": round(p.fps, 1),
                    "running": p.is_running,
                }
                for cid, p in self._pipelines.items()
            },
        }
