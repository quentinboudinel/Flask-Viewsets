# noqa: D100
# ruff: noqa: D101
# ruff: noqa: D102
# ruff: noqa: D107
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from lark import Lark

from .transformers import WhereTransformer

if TYPE_CHECKING:
    from sqlalchemy import ColumnElement

    from flask_viewsets.typing import Model

GRAMMARS_DIR = Path(__file__).parent / "grammars"


class WhereParser:
    def __init__(self, model: type[Model]) -> None:
        with Path.open(GRAMMARS_DIR / "where.lark") as f:
            grammar = f.read()
        self.lark = Lark(  # type: ignore[partially-unknown]
            grammar,
            parser="lalr",
            start="where",
            transformer=WhereTransformer(model),
        )

    def parse(self, where: str) -> ColumnElement[bool]:
        return self.lark.parse(where)  # type: ignore[not-assignable-to-return-type]
