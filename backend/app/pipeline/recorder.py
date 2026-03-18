import asyncio
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class SegmentRecorderConfig:
    """Configuration for the FFmpeg segment recorder."""

    def __init__(
        self,
        output_dir: str = "/recordings",
        segment_duration: int = 60,  # seconds per segment
        retention_hours: int = 72,  # hours to keep recordings
        video_codec: str = "copy",  # "copy" for passthrough, "libx264" for re-encode
    ):
        self.output_dir = output_dir
        self.segment_duration = segment_duration
        self.retention_hours = retention_hours
        self.video_codec = video_codec


class SegmentRecorder:
    """Records RTSP stream as segmented files using FFmpeg."""

    def __init__(
        self,
        camera_id: str,
        rtsp_url: str,
        config: SegmentRecorderConfig | None = None,
    ) -> None:
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.config = config or SegmentRecorderConfig()
        self._process: subprocess.Popen | None = None
        self._running = False
        self._camera_dir = Path(self.config.output_dir) / camera_id

    async def start(self) -> None:
        """Start recording in the background."""
        self._camera_dir.mkdir(parents=True, exist_ok=True)
        self._running = True

        segment_pattern = str(self._camera_dir / "%Y%m%d_%H%M%S.mp4")

        cmd = [
            "ffmpeg",
            "-rtsp_transport",
            "tcp",
            "-i",
            self.rtsp_url,
            "-c:v",
            self.config.video_codec,
            "-an",  # No audio
            "-f",
            "segment",
            "-segment_time",
            str(self.config.segment_duration),
            "-segment_format",
            "mp4",
            "-strftime",
            "1",
            "-reset_timestamps",
            "1",
            "-y",
            segment_pattern,
        ]

        self._process = await asyncio.to_thread(
            subprocess.Popen,
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        logger.info(
            "Recording started for camera %s -> %s", self.camera_id, self._camera_dir
        )

        # Start cleanup task
        asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop recording."""
        self._running = False
        if self._process:
            self._process.terminate()
            try:
                await asyncio.to_thread(self._process.wait, timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
            logger.info("Recording stopped for camera %s", self.camera_id)

    async def _cleanup_loop(self) -> None:
        """Periodically remove old recordings."""
        while self._running:
            try:
                await self._cleanup_old_segments()
            except Exception as e:
                logger.error("Cleanup error for camera %s: %s", self.camera_id, e)
            await asyncio.sleep(300)  # Check every 5 minutes

    async def _cleanup_old_segments(self) -> None:
        """Delete segments older than retention period."""
        cutoff = datetime.now() - timedelta(hours=self.config.retention_hours)
        removed = 0
        for f in self._camera_dir.glob("*.mp4"):
            try:
                # Parse timestamp from filename: 20260318_030000.mp4
                ts_str = f.stem
                file_time = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                if file_time < cutoff:
                    f.unlink()
                    removed += 1
            except (ValueError, OSError):
                continue
        if removed > 0:
            logger.info(
                "Cleaned up %d old segments for camera %s", removed, self.camera_id
            )

    def get_segments_in_range(self, start: datetime, end: datetime) -> list[Path]:
        """Get recording segments that overlap with a time range."""
        segments = []
        for f in sorted(self._camera_dir.glob("*.mp4")):
            try:
                ts_str = f.stem
                file_time = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                file_end = file_time + timedelta(seconds=self.config.segment_duration)
                if file_time <= end and file_end >= start:
                    segments.append(f)
            except ValueError:
                continue
        return segments

    @property
    def is_running(self) -> bool:
        """Check if the FFmpeg process is still running."""
        if self._process is None:
            return False
        return self._process.poll() is None
