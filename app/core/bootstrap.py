from collections.abc import Sequence

from celery import Celery
from fastapi import FastAPI

from app.core.config import Settings
from app.core.registry import ModuleContract, ModuleRegistry


def load_modules(*, settings: Settings) -> list[ModuleContract]:
    registry = ModuleRegistry(settings=settings)
    return registry.load_modules()


def bootstrap_app(*, app: FastAPI, settings: Settings) -> Sequence[ModuleContract]:
    modules = load_modules(settings=settings)
    for module in modules:
        app.include_router(module.register_routes(), prefix=settings.api_prefix)
    return modules


def bootstrap_celery_tasks(*, celery_app: Celery, settings: Settings) -> list[object]:
    registered_tasks: list[object] = []
    for module in load_modules(settings=settings):
        for task in module.register_tasks():
            celery_app.tasks.register(task)
            registered_tasks.append(task)
    return registered_tasks
