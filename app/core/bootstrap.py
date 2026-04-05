from app.core.celery_app import celery_app
from fastapi import FastAPI

from app.core.config import Settings
from app.core.registry import ModuleRegistry


def bootstrap_app(*, app: FastAPI, settings: Settings) -> list[object]:
    registry = ModuleRegistry(settings=settings)
    modules = registry.load_modules()
    for module in modules:
        app.include_router(module.register_routes(), prefix=settings.api_prefix)
        for task in module.register_tasks():
            celery_app.tasks.register(task)
    return modules
