"""SQLAlchemy declarative base class and metadata configuration."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Uniform naming conventions for constraints to simplify Alembic migrations
POSTGRES_INDEX_NAMING_CONVENTIONS = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=POSTGRES_INDEX_NAMING_CONVENTIONS)


class Base(DeclarativeBase):
    """Base class for all future SQLAlchemy database models."""
    metadata = metadata
