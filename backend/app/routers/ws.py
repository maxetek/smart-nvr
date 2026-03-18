import asyncio
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth.jwt import decode_token
from app.config import settings
from app.database import async_session
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

REALTIME_CHANNEL = "smartnvr:realtime"


async def _validate_ws_token(websocket: WebSocket) -> User | None:
    """Validate JWT from query param on WebSocket connect."""
    token = websocket.query_params.get("token")
    if not token:
        return None
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if user_id is None:
            return None
        async with async_session() as db:
            user = await db.get(User, uuid.UUID(user_id))
            if user is None or not user.is_active:
                return None
            return user
    except Exception:
        return None


@router.websocket("/ws/events")
async def ws_events(websocket: WebSocket) -> None:
    user = await _validate_ws_token(websocket)
    if user is None:
        await websocket.close(code=4001, reason="Authentication required")
        return

    await websocket.accept()
    logger.info("WebSocket client connected: user=%s", user.username)

    try:
        import redis.asyncio as aioredis

        redis_conn = aioredis.from_url(settings.redis_url, decode_responses=True)
        pubsub = redis_conn.pubsub()
        await pubsub.subscribe(REALTIME_CHANNEL)

        try:
            while True:
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                    timeout=5.0,
                )
                if message and message["type"] == "message":
                    await websocket.send_text(message["data"])
        except asyncio.TimeoutError:
            pass
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected: user=%s", user.username)
        finally:
            await pubsub.unsubscribe(REALTIME_CHANNEL)
            await pubsub.aclose()
            await redis_conn.aclose()
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected: user=%s", user.username)
    except Exception:
        logger.exception("WebSocket error for user=%s", user.username)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
