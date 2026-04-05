from collections.abc import Callable
from importlib import import_module
from pkgutil import iter_modules
from types import ModuleType
from typing import Protocol

from fastapi import APIRouter

from app.core.config import Settings


class ModuleContract(Protocol):
    name: str

    def register_routes(self) -> APIRouter: ...

    def register_tasks(self) -> list[Callable[..., object]]: ...


class ModuleRegistry:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings

    def _load_from_path(self, import_path: str) -> ModuleContract:
        module: ModuleType = import_module(import_path)
        return module.Module()

    def _discover_modules(self) -> list[str]:
        if not self.settings.auto_discover_modules:
            return []

        import app.modules as package

        return [
            f"app.modules.{entry.name}.module"
            for entry in iter_modules(package.__path__)
            if entry.name != "__pycache__"
        ]

    def load_modules(self) -> list[ModuleContract]:
        module_paths = list(dict.fromkeys(self.settings.enabled_modules + self._discover_modules()))
        return [self._load_from_path(path) for path in module_paths]
