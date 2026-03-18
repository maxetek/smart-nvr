import logging

from app.pipeline.attributes.base import AttributeModel

logger = logging.getLogger(__name__)


class AttributeModelRegistry:
    """Plugin registry for attribute models. Supports runtime register/unregister."""

    def __init__(self) -> None:
        self._models: dict[str, AttributeModel] = {}

    def register(self, model: AttributeModel) -> None:
        model.load()
        self._models[model.name] = model
        logger.info("Registered attribute model: %s", model.name)

    def unregister(self, name: str) -> None:
        if name in self._models:
            self._models[name].unload()
            del self._models[name]
            logger.info("Unregistered attribute model: %s", name)

    def get(self, name: str) -> AttributeModel | None:
        return self._models.get(name)

    def get_for_class(self, class_name: str) -> list[AttributeModel]:
        return [m for m in self._models.values() if class_name in m.target_classes]

    @property
    def all_models(self) -> dict[str, AttributeModel]:
        return self._models.copy()

    def unload_all(self) -> None:
        for name in list(self._models.keys()):
            self.unregister(name)
