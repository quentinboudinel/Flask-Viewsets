"""Module providing classes and functions for handling model based viewsets."""

from __future__ import annotations

from abc import ABCMeta
from collections.abc import Callable, Generator, Sequence
from typing import TYPE_CHECKING, Any, cast

from flask import abort, request
from sqlalchemy import ColumnExpressionArgument, select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from flask_viewsets.viewsets import ViewSet

from .parsers import WhereParser

if TYPE_CHECKING:
    from flask.typing import ResponseReturnValue
    from flask_sqlalchemy import SQLAlchemy

    from flask_viewsets.extension import ViewSets
    from flask_viewsets.typing import Model, ModelSchema


class AbstractBaseModelViewSet[M: Model](ViewSet, metaclass=ABCMeta):
    """A viewset that provides default implementations for model CRUD operations."""

    model: type[M]  # ClassVar[type[M]]
    schema_cls: (
        Callable[[], ModelSchema[M]] | type[ModelSchema[M]]
    )  # ClassVar[type[ModelSchema[M]]]
    db: SQLAlchemy
    vs: ViewSets

    @property
    def schema(self) -> ModelSchema[M]:
        """Return the schema instance."""
        return self.get_schema()

    @property
    def where_clause(self) -> Generator[ColumnExpressionArgument[bool], None, None]:
        """Generate the where clause for request arguments based filtering."""
        if request.view_args:
            for name, value in request.view_args.items():
                yield getattr(self.model, name) == value
        if where := request.args.get("where"):
            yield WhereParser(model=self.model).parse(where)

    @property
    def order_by_clause(self) -> Generator[ColumnExpressionArgument[Any], None, None]:
        """Generate the order by clause for request arguments based sorting."""
        if order_by := request.args.get("order_by"):
            for field in order_by.split(","):
                if field.startswith("-"):
                    yield getattr(self.model, field[1:]).desc()
                else:
                    yield getattr(self.model, field)

    @property
    def limit(self) -> int | None:
        """Return the limit for the query from request arguments."""
        requested_limit = request.args.get("limit", type=int)
        max_limit = self.vs.config.get("max_limit")
        return (
            min(requested_limit, max_limit)
            if (requested_limit and max_limit)
            else (max_limit or requested_limit)
        )

    @property
    def offset(self) -> int | None:
        """Return the offset for the query from request arguments."""
        return request.args.get("offset", type=int)

    def get_schema(self) -> ModelSchema[M]:
        """Return the schema instance."""
        return self.schema_cls()

    def get_instances(self) -> Sequence[M]:
        """Return the instances based on the query."""
        stmt = (
            select(self.model)
            .where(*self.where_clause)
            .order_by(*self.order_by_clause)
            .limit(self.limit)
            .offset(self.offset)
        )
        return self.db.session.execute(stmt).scalars().all()

    def get_instance(self) -> M:
        """Return the instance based on the query."""
        stmt = select(self.model).where(*self.where_clause)
        try:
            instance = self.db.session.execute(stmt).scalars().one()
        except NoResultFound:
            self.db.session.rollback()
            abort(404)
        except MultipleResultsFound:
            self.db.session.rollback()
            abort(500)
        return instance

    def dump(self, instance: M | Sequence[M]) -> dict[str, Any] | list[dict[str, Any]]:
        """Serialize the instance or instances using the schema."""
        if isinstance(instance, Sequence):
            return self.schema.dump(instance, many=True)  # type: ignore[partially-unknown]
        return self.schema.dump(instance)  # type: ignore[partially-unknown]

    def create(self) -> ResponseReturnValue:
        """Create a new instance of the model."""
        data = request.get_json()
        instance = cast(M, self.schema.load(data))  # type: ignore[partially-unknown]
        self.db.session.add(instance)
        self.db.session.commit()
        return self.dump(instance), 201

    def list(self, **_: Any) -> ResponseReturnValue:  # noqa: ANN401
        """List serialized instances of the model."""
        instances = self.get_instances()
        return self.dump(instances), 200

    def retrieve(self, **_: Any) -> ResponseReturnValue:  # noqa: ANN401
        """Retrieve an existing instance of the model."""
        instance = self.get_instance()
        return self.dump(instance), 200

    def update(self, **_: Any) -> ResponseReturnValue:  # noqa: ANN401
        """Update an existing instance of the model."""
        data = request.get_json()
        instance = self.get_instance()
        instance = cast(M, self.schema.load(data, instance=instance))  # type: ignore[partially-unknown]
        self.db.session.commit()
        return self.dump(instance), 200

    def partial_update(self, **_: Any) -> ResponseReturnValue:  # noqa: ANN401
        """Update partially an existing instance of the model."""
        data = request.get_json()
        instance = self.get_instance()
        instance = cast(M, self.schema.load(data, instance=instance, partial=True))  # type: ignore[partially-unknown]
        self.db.session.commit()
        return self.dump(instance), 200

    def destroy(self, **_: Any) -> ResponseReturnValue:  # noqa: ANN401
        """Delete an existing instance of the model."""
        instance = self.get_instance()
        self.db.session.delete(instance)
        self.db.session.commit()
        return b"", 204
