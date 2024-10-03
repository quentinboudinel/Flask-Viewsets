from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    ColumnElement,
    Engine,
    Integer,
    and_,
    create_engine,
    not_,
    or_,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from flask_viewsets.parsers import WhereParser

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import CompilerElement

    from flask_viewsets.typing import Model


@pytest.fixture
def engine():
    return create_engine("sqlite:///:memory:")


@pytest.fixture
def db():
    return SQLAlchemy()


@pytest.fixture
def model(db: SQLAlchemy) -> type[Model]:
    class TestModel(db.Model):
        __tablename__ = "test"

        id: Mapped[int] = mapped_column(primary_key=True)
        array: Mapped[list[int]] = mapped_column(
            ARRAY(Integer),
            default=lambda: [1, 2, 3],
        )

    return TestModel


@pytest.fixture
def where_parser(model: type[Model]):
    return WhereParser(model)


def test_parse(engine: Engine, model: type[Model], where_parser: WhereParser):
    def compile_(stmt: CompilerElement) -> str:
        return str(stmt.compile(engine, compile_kwargs={"literal_binds": True}))

    def compare(where_string: str, where_clause: ColumnElement[bool]) -> bool:
        return compile_(where_parser.parse(where_string)) == compile_(where_clause)

    id_column = cast(ColumnElement[int], model.id)  # type: ignore[attr-defined]
    array_column = cast(ColumnElement[list[int]], model.array)  # type: ignore[attr-defined]

    assert compare("id=1", id_column == 1)
    assert compare("id=null", id_column.is_(None))
    assert compare("id!=1", id_column != 1)
    assert compare("!(id=null)", id_column.is_not(None))
    assert compare("!(id=null)", not_(id_column.is_(None)))
    assert compare("id>1", id_column > 1)
    assert compare("id>=1", id_column >= 1)
    assert compare("id<1", id_column < 1)
    assert compare("id<=1", id_column <= 1)
    assert compare("id=1&id=2", and_(id_column == 1, id_column == 2))
    assert compare("id=1|id=2", or_(id_column == 1, id_column == 2))
    assert compare(
        "id=1|id=2&id=3",
        or_(id_column == 1, and_(id_column == 2, id_column == 3)),
    )
    assert compare(
        "(id=1|id=2)&id=3",
        and_(or_(id_column == 1, id_column == 2), id_column == 3),
    )
    assert compare("array#1", array_column.contains(1))
    assert compare("id@[1,2,3]", id_column.in_([1, 2, 3]))
