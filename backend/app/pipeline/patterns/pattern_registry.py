from app.pipeline.patterns.base import BasePattern
from app.pipeline.patterns.ml_based.smoking_pattern import SmokingPattern
from app.pipeline.patterns.ml_based.weapon_pattern import WeaponPattern
from app.pipeline.patterns.rule_based.crowd_density import CrowdDensityPattern
from app.pipeline.patterns.rule_based.line_crossing import LineCrossingPattern
from app.pipeline.patterns.rule_based.loitering import LoiteringPattern
from app.pipeline.patterns.rule_based.zone_intrusion import ZoneIntrusionPattern

PATTERN_TYPES: dict[str, type[BasePattern]] = {
    "line_cross": LineCrossingPattern,
    "zone_intrusion": ZoneIntrusionPattern,
    "loitering": LoiteringPattern,
    "crowd": CrowdDensityPattern,
    "smoking": SmokingPattern,
    "weapon": WeaponPattern,
}


def create_pattern(
    pattern_id: str,
    camera_id: str,
    name: str,
    pattern_type: str,
    config: dict,
    cooldown_seconds: int = 60,
) -> BasePattern:
    """Factory function to create pattern instances from database config."""
    cls = PATTERN_TYPES.get(pattern_type)
    if cls is None:
        raise ValueError(f"Unknown pattern type: {pattern_type}")
    return cls(
        pattern_id=pattern_id,
        camera_id=camera_id,
        name=name,
        pattern_type=pattern_type,
        config=config,
        cooldown_seconds=cooldown_seconds,
    )
