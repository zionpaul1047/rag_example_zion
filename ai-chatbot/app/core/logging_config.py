import logging

from app.core.settings import settings


def _resolve_log_level(level_name: str) -> int:
    level = logging.getLevelName((level_name or "").strip().upper())

    if isinstance(level, int):
        return level

    return logging.INFO


def configure_logging() -> None:
    logging.basicConfig(
        level=_resolve_log_level(settings.LOG_LEVEL),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
