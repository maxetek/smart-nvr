import asyncio
import logging
import time
from dataclasses import dataclass

import numpy as np

from app.pipeline.detector.yolo_detector import DetectorConfig, YOLODetector
from app.pipeline.event_publisher import EventPublisher
from app.pipeline.frame_grabber import FrameGrabber, FrameGrabberConfig
from app.pipeline.models.track import TrackState
from app.pipeline.recorder import SegmentRecorder, SegmentRecorderConfig
from app.pipeline.state_machine import TrackStateMachine
from app.pipeline.tracker.bytetrack_tracker import ByteTrackConfig, ByteTrackTracker

logger = logging.getLogger(__name__)


@dataclass
class CameraPipelineConfig:
    """Configuration for a single camera pipeline."""

    camera_id: str
    camera_name: str
    rtsp_url: str
    sub_stream_url: str | None = None  # Low-res stream for detection
    target_fps: int = 15  # Process at this FPS
    enable_recording: bool = True
    detector_config: DetectorConfig | None = None
    tracker_config: ByteTrackConfig | None = None
    recorder_config: SegmentRecorderConfig | None = None


class CameraPipeline:
    """Per-camera processing pipeline: grab -> detect -> track -> publish."""

    def __init__(
        self,
        config: CameraPipelineConfig,
        detector: YOLODetector,  # Shared across cameras
    ) -> None:
        self.config = config
        self._detector = detector

        # Use sub-stream for detection if available, main stream for recording
        detect_url = config.sub_stream_url or config.rtsp_url
        self._grabber = FrameGrabber(FrameGrabberConfig(url=detect_url))
        self._tracker = ByteTrackTracker(config.tracker_config)
        self._state_machine = TrackStateMachine()
        self._publisher = EventPublisher(camera_id=config.camera_id)
        self._recorder: SegmentRecorder | None = None

        if config.enable_recording:
            self._recorder = SegmentRecorder(
                camera_id=config.camera_id,
                rtsp_url=config.rtsp_url,  # Record from main stream
                config=config.recorder_config,
            )

        self._running = False
        self._fps = 0.0
        self._frame_count = 0
        self._last_fps_time = time.time()

    async def start(self) -> None:
        """Start the pipeline."""
        self._running = True
        logger.info(
            "Starting pipeline for camera %s (%s)",
            self.config.camera_id,
            self.config.camera_name,
        )

        # Start recorder
        if self._recorder:
            await self._recorder.start()

        # Process frames
        frame_interval = 1.0 / self.config.target_fps
        last_process_time = 0.0

        async for frame, timestamp in self._grabber.frames():
            if not self._running:
                break

            # Frame skip: only process at target FPS
            now = time.time()
            if now - last_process_time < frame_interval:
                continue
            last_process_time = now

            try:
                await self._process_frame(frame, timestamp)
            except Exception as e:
                logger.error(
                    "Frame processing error on camera %s: %s", self.config.camera_id, e
                )

            # Update FPS counter
            self._frame_count += 1
            if now - self._last_fps_time >= 1.0:
                self._fps = self._frame_count / (now - self._last_fps_time)
                self._frame_count = 0
                self._last_fps_time = now

    async def _process_frame(self, frame: np.ndarray, timestamp: float) -> None:
        """Process a single frame: detect -> track -> state transitions -> publish events."""
        # 1. Detect
        detections = await asyncio.to_thread(self._detector.detect, frame)

        # 2. Track
        active_tracks = self._tracker.update(detections)
        active_track_ids = {t.track_id for t in active_tracks}

        # 3. State transitions + event publishing
        all_tracks = self._tracker.get_all_tracks()
        for tid, track in all_tracks.items():
            is_detected = tid in active_track_ids
            new_state = self._state_machine.update(track, is_detected)

            if new_state is not None:
                # State changed — publish event
                if new_state == TrackState.INITIAL:
                    await self._publisher.publish_new_track(track)
                elif new_state == TrackState.TRACKING:
                    await self._publisher.publish_track_confirmed(track)
                elif new_state == TrackState.DEAD:
                    await self._publisher.publish_track_lost(track)

    async def stop(self) -> None:
        """Stop the pipeline."""
        self._running = False
        self._grabber.stop()
        if self._recorder:
            await self._recorder.stop()
        logger.info("Pipeline stopped for camera %s", self.config.camera_id)

    @property
    def fps(self) -> float:
        """Return current processing FPS."""
        return self._fps

    @property
    def is_running(self) -> bool:
        """Return whether the pipeline is running."""
        return self._running
