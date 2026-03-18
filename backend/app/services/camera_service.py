import uuid

from cryptography.fernet import Fernet
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.camera import Camera
from app.schemas.camera import CameraCreate, CameraUpdate


def _get_fernet() -> Fernet:
    key = settings.encryption_key
    if len(key) != 44:
        # Pad or derive a valid Fernet key from the settings value
        import base64
        import hashlib

        derived = hashlib.sha256(key.encode()).digest()
        key = base64.urlsafe_b64encode(derived).decode()
    return Fernet(key.encode())


def encrypt_url(url: str) -> str:
    return _get_fernet().encrypt(url.encode()).decode()


def decrypt_url(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()


async def create_camera(db: AsyncSession, data: CameraCreate) -> Camera:
    camera = Camera(
        name=data.name,
        rtsp_url_encrypted=encrypt_url(data.rtsp_url),
        sub_stream_url_encrypted=encrypt_url(data.sub_stream_url) if data.sub_stream_url else None,
        location=data.location,
        width=data.width,
        height=data.height,
        fps=data.fps,
    )
    db.add(camera)
    await db.flush()
    await db.refresh(camera)
    return camera


async def get_camera(db: AsyncSession, camera_id: uuid.UUID) -> Camera | None:
    return await db.get(Camera, camera_id)


async def list_cameras(
    db: AsyncSession, limit: int = 20, offset: int = 0
) -> tuple[list[Camera], int]:
    total_result = await db.execute(select(func.count()).select_from(Camera))
    total = total_result.scalar_one()

    result = await db.execute(
        select(Camera).order_by(Camera.created_at.desc()).limit(limit).offset(offset)
    )
    cameras = list(result.scalars().all())
    return cameras, total


async def update_camera(
    db: AsyncSession, camera_id: uuid.UUID, data: CameraUpdate
) -> Camera | None:
    camera = await db.get(Camera, camera_id)
    if camera is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    if "rtsp_url" in update_data:
        camera.rtsp_url_encrypted = encrypt_url(update_data.pop("rtsp_url"))
    if "sub_stream_url" in update_data:
        val = update_data.pop("sub_stream_url")
        camera.sub_stream_url_encrypted = encrypt_url(val) if val else None

    for key, value in update_data.items():
        setattr(camera, key, value)

    await db.flush()
    await db.refresh(camera)
    return camera


async def delete_camera(db: AsyncSession, camera_id: uuid.UUID) -> bool:
    camera = await db.get(Camera, camera_id)
    if camera is None:
        return False
    await db.delete(camera)
    await db.flush()
    return True
