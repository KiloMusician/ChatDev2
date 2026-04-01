"""Lightweight project/artifact models with optional SQLAlchemy helpers."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

Base = object


@dataclass
class Project:
    """Portable project model used by API and migration scripts."""

    id: int | None = None
    name: str = ""
    description: str | None = None


@dataclass
class Artifact:
    """Portable artifact model used by API and migration scripts."""

    id: int | None = None
    name: str = ""
    file_path: str = ""
    project_id: int | None = None


def get_engine(url: str = "sqlite:///project_management.db") -> Any | None:
    """Return a SQLAlchemy engine when SQLAlchemy is installed, else None."""
    try:
        sqlalchemy = importlib.import_module("sqlalchemy")
        create_engine = getattr(sqlalchemy, "create_engine", None)
        if callable(create_engine):
            return create_engine(url)
    except ImportError:
        return None
    return None


def get_session(url: str = "sqlite:///project_management.db") -> Any | None:
    """Return a SQLAlchemy session when SQLAlchemy is installed, else None."""
    try:
        orm_module = importlib.import_module("sqlalchemy.orm")
        sessionmaker = getattr(orm_module, "sessionmaker", None)
        if callable(sessionmaker):
            engine = get_engine(url)
            if engine is not None:
                return sessionmaker(bind=engine)()
    except ImportError:
        return None
    return None


__all__ = ["Artifact", "Base", "Project", "get_engine", "get_session"]
