import asyncio
import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass

import av
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FrameGrabberConfig:
    """Configuration for the RTSP frame grabber."""

    url: str  # RTSP URL
    reconnect_delay: float = 5.0  # Seconds between reconnect attempts
    max_reconnect_attempts: int = 0  # 0 = infinite
    timeout: float = 10.0  # Connection timeout
    thread_count: int = 1  # Decoder threads


class FrameGrabber:
    """Async RTSP frame reader using PyAV with reconnect logic."""

    def __init__(self, config: FrameGrabberConfig) -> None:
        self.config = config
        self._container = None
        self._running = False
        self._reconnect_count = 0

    async def frames(self) -> AsyncIterator[tuple[np.ndarray, float]]:
        """Yield (frame, timestamp) tuples from the RTSP stream."""
        self._running = True

        while self._running:
            try:
                # Open in a thread to not block the event loop
                self._container = await asyncio.to_thread(
                    self._open_container, self.config.url
                )
                self._reconnect_count = 0
                logger.info("Connected to stream: %s", self._mask_url(self.config.url))

                stream = self._container.streams.video[0]
                stream.thread_type = "AUTO"
                stream.thread_count = self.config.thread_count

                for frame in self._container.decode(stream):
                    if not self._running:
                        break
                    img = frame.to_ndarray(format="bgr24")
                    timestamp = (
                        float(frame.pts * stream.time_base) if frame.pts else time.time()
                    )
                    yield img, timestamp
                    # Yield control to event loop
                    await asyncio.sleep(0)

            except av.error.EOFError:
                logger.warning("Stream ended: %s", self._mask_url(self.config.url))
            except Exception as e:
                logger.error("Stream error: %s — %s", self._mask_url(self.config.url), e)
            finally:
                self._close_container()

            # Reconnect logic
            if not self._running:
                break
            self._reconnect_count += 1
            if (
                self.config.max_reconnect_attempts > 0
                and self._reconnect_count > self.config.max_reconnect_attempts
            ):
                logger.error(
                    "Max reconnect attempts reached for %s",
                    self._mask_url(self.config.url),
                )
                break

            logger.info(
                "Reconnecting in %.1fs (attempt %d)...",
                self.config.reconnect_delay,
                self._reconnect_count,
            )
            await asyncio.sleep(self.config.reconnect_delay)

    def _open_container(self, url: str):
        """Open an RTSP container (runs in thread)."""
        options = {
            "rtsp_transport": "tcp",
            "stimeout": str(int(self.config.timeout * 1_000_000)),  # microseconds
        }
        return av.open(url, options=options, timeout=self.config.timeout)

    def _close_container(self) -> None:
        """Close the current container if open."""
        if self._container:
            try:
                self._container.close()
            except Exception:
                pass
            self._container = None

    def stop(self) -> None:
        """Stop the frame grabber."""
        self._running = False
        self._close_container()

    @staticmethod
    def _mask_url(url: str) -> str:
        """Mask credentials in RTSP URL for logging."""
        if "@" in url:
            parts = url.split("@")
            return f"rtsp://***@{parts[-1]}"
        return url
