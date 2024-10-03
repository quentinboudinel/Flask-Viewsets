# noqa: D100
# ruff: noqa: D102
# ruff: noqa: N802

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lark import Token, Transformer
from sqlalchemy import ColumnElement, and_, not_, or_

if TYPE_CHECKING:
    from flask_viewsets.typing import Model

type Value = None | bool | float | int | str | list[Value] | dict[str, Value]


class WhereTransformer(Transformer[Token, ColumnElement[bool]]):
    """Transformer for parsing 'where' url param into SQLAlchemy expressions."""

    def __init__(self, model: type[Model]) -> None:
        """Initialize the WhereTransformer with the given model.

        :param model: The SQLAlchemy model to be used for transformations.
        """
        super().__init__()
        self.model = model

    def NAME(self, name: Token) -> ColumnElement[Any]:
        return getattr(self.model, name)

    def NULL(self, _: Token) -> None:
        return None

    def TRUE(self, _: Token) -> bool:
        return True

    def FALSE(self, _: Token) -> bool:
        return False

    def NUMBER(self, number: Token) -> float:
        try:
            return int(number)
        except ValueError:
            return float(number)

    def STRING(self, string: Token) -> str:
        return string[1:-1]

    def array(
        self,
        args: list[Value],
    ) -> list[Value]:
        return [*args]

    def PAIR(self, args: tuple[str, Value]) -> tuple[str, Value]:
        return args

    def object(self, args: list[tuple[str, Value]]) -> dict[str, Value]:
        return dict(args)

    def or_(self, clauses: list[ColumnElement[bool]]) -> ColumnElement[bool]:
        return or_(*clauses)

    def and_(self, clauses: list[ColumnElement[bool]]) -> ColumnElement[bool]:
        return and_(*clauses)

    def not_(self, args: list[ColumnElement[bool]]) -> ColumnElement[bool]:
        return not_(*args)

    def eq(self, args: tuple[ColumnElement[Any], Value]) -> ColumnElement[bool]:
        if args[1] is None:
            return args[0].is_(None)
        return args[0] == args[1]

    def ne(self, args: tuple[ColumnElement[Any], Value]) -> ColumnElement[bool]:
        return args[0] != args[1]

    def gt(self, args: tuple[ColumnElement[Any], Value]) -> ColumnElement[bool]:
        return args[0] > args[1]

    def ge(self, args: tuple[ColumnElement[Any], Value]) -> ColumnElement[bool]:
        return args[0] >= args[1]

    def lt(self, args: tuple[ColumnElement[Any], Value]) -> ColumnElement[bool]:
        return args[0] < args[1]

    def le(self, args: tuple[ColumnElement[Any], Value]) -> ColumnElement[bool]:
        return args[0] <= args[1]

    def contains(self, args: tuple[ColumnElement[str], Value]) -> ColumnElement[bool]:
        return args[0].contains(args[1])

    def in_(self, args: tuple[ColumnElement[Any], list[Value]]) -> ColumnElement[bool]:
        return args[0].in_(args[1])
