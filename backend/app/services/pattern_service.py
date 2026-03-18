import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pattern import Pattern
from app.schemas.pattern import PatternCreate, PatternUpdate


async def create_pattern(db: AsyncSession, data: PatternCreate) -> Pattern:
    pattern = Pattern(
        camera_id=data.camera_id,
        name=data.name,
        pattern_type=data.pattern_type,
        config_json=data.config_json,
        cooldown_seconds=data.cooldown_seconds,
        is_enabled=data.is_enabled,
    )
    db.add(pattern)
    await db.flush()
    await db.refresh(pattern)
    return pattern


async def get_pattern(db: AsyncSession, pattern_id: uuid.UUID) -> Pattern | None:
    return await db.get(Pattern, pattern_id)


async def list_patterns(
    db: AsyncSession,
    camera_id: uuid.UUID | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Pattern], int]:
    base = select(Pattern)
    count_q = select(func.count()).select_from(Pattern)

    if camera_id is not None:
        base = base.where(Pattern.camera_id == camera_id)
        count_q = count_q.where(Pattern.camera_id == camera_id)

    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    result = await db.execute(
        base.order_by(Pattern.created_at.desc()).limit(limit).offset(offset)
    )
    patterns = list(result.scalars().all())
    return patterns, total


async def update_pattern(
    db: AsyncSession, pattern_id: uuid.UUID, data: PatternUpdate
) -> Pattern | None:
    pattern = await db.get(Pattern, pattern_id)
    if pattern is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pattern, key, value)

    await db.flush()
    await db.refresh(pattern)
    return pattern


async def delete_pattern(db: AsyncSession, pattern_id: uuid.UUID) -> bool:
    pattern = await db.get(Pattern, pattern_id)
    if pattern is None:
        return False
    await db.delete(pattern)
    await db.flush()
    return True
