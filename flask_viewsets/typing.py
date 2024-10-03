"""Module defining type annotations for the Flask-Viewsets project.

This module provides type annotations to be used throughout the Flask-Viewsets
project, ensuring type consistency and clarity.

Types:
    ConverterType: A union type that can be an int, float, str, or UUID.
    Schema: A union type that can be either SQLAlchemySchema or SQLAlchemyAutoSchema.

Exports:
    ConverterType: Type alias for int | float | str | UUID.
    Model: Alias for flask_sqlalchemy.model.Model.
    Schema: Type alias for SQLAlchemySchema | SQLAlchemyAutoSchema.
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from flask.typing import RouteCallable
from flask_marshmallow.sqla import SQLAlchemyAutoSchema, SQLAlchemySchema
from flask_sqlalchemy.model import Model

type ConverterType = int | float | str | UUID
type RouteDecorator = Callable[[RouteCallable], RouteCallable]
type ModelSchema[M: Model] = SQLAlchemySchema | SQLAlchemyAutoSchema

__all__ = ("ConverterType", "Model", "RouteDecorator", "ModelSchema")
