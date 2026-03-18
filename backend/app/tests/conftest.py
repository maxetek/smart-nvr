import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.jwt import create_access_token
from app.auth.password import hash_password
from app.database import get_db
from app.models import Base
from app.models.camera import Camera
from app.models.event import Event
from app.models.user import User

# Use SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    from app.main import app

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def admin_user(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        username="testadmin",
        email="admin@test.com",
        password_hash=hash_password("AdminPass123"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest.fixture
async def operator_user(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        username="testoperator",
        email="operator@test.com",
        password_hash=hash_password("OperatorPass123"),
        role="operator",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest.fixture
async def viewer_user(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        username="testviewer",
        email="viewer@test.com",
        password_hash=hash_password("ViewerPass123"),
        role="viewer",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


def make_auth_headers(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict[str, str]:
    return make_auth_headers(admin_user)


@pytest.fixture
def operator_headers(operator_user: User) -> dict[str, str]:
    return make_auth_headers(operator_user)


@pytest.fixture
def viewer_headers(viewer_user: User) -> dict[str, str]:
    return make_auth_headers(viewer_user)


@pytest.fixture
async def sample_camera(db: AsyncSession) -> Camera:
    from app.services.camera_service import encrypt_url

    camera = Camera(
        id=uuid.uuid4(),
        name="Test Camera 1",
        rtsp_url_encrypted=encrypt_url("rtsp://test:554/stream"),
        location="Front Door",
        is_enabled=True,
    )
    db.add(camera)
    await db.flush()
    await db.refresh(camera)
    return camera


@pytest.fixture
async def sample_event(db: AsyncSession, sample_camera: Camera) -> Event:
    event = Event(
        id=uuid.uuid4(),
        camera_id=sample_camera.id,
        event_type="line_cross",
        severity="warning",
        confidence=0.95,
        is_acknowledged=False,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event
