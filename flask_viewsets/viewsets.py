"""Module defining a base class for creating viewsets in Flask.

Classes:
    ViewSet: A base class for creating viewsets in Flask, mapping HTTP methods to class
        methods.

Type Aliases:
    RouteDecorator: A callable that takes a RouteCallable and returns a RouteCallable.
    ActionDecorators: A dictionary mapping action names to iterables of RouteDecorators.
"""

from __future__ import annotations

from abc import ABCMeta
from collections.abc import Callable, Generator, Sequence
from typing import TYPE_CHECKING, Any, ClassVar, cast

from flask import abort, current_app, request
from flask.views import View
from sqlalchemy import ColumnExpressionArgument, select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from .parsers import WhereParser

if TYPE_CHECKING:
    from collections.abc import Iterable

    from flask.typing import ResponseReturnValue, RouteCallable
    from flask_sqlalchemy import SQLAlchemy

    from flask_viewsets.extension import ViewSets
    from flask_viewsets.typing import Model, ModelSchema

    from .typing import ConverterType, RouteDecorator


class ViewSet(View, metaclass=ABCMeta):
    """ViewSet class for handling HTTP method actions in a Flask application.

    Attributes:
        action_decorators (ClassVar[ActionDecorators]): A dictionary of decorators to be
            applied to actions.

    Methods:
        __init__(method_actions: dict[str, str]) -> None:
            Initialize the ViewSet with method actions.
        dispatch_request(**kwargs: ConverterType) -> ResponseReturnValue:
            Dispatch the request to the appropriate method action.
        as_view(
            *class_args: Any,
            **class_kwargs: Any
            Generate view from ViewSet.

    """

    action_decorators: ClassVar[dict[str, Iterable[RouteDecorator]]] = {}
    method_actions: dict[str, str]
    vs: ViewSets

    def __init__(self, method_actions: dict[str, str]) -> None:
        """Initialize the viewset with the given method actions.

        Args:
            method_actions (dict[str, str]): A dictionary mapping HTTP methods to action
                names.

        """
        super().__init__()
        self.method_actions = method_actions

    def dispatch_request(self, **kwargs: ConverterType) -> ResponseReturnValue:
        """Dispatches request to appropriate handler method based on HTTP method.

        This method determines the action to be taken based on the HTTP method of the
        request. If the action is not defined for the HTTP method, it will check if a
        'head' request can be handled by the 'get' method. If no appropriate action is
        found, it aborts with a 405 status code. If the action is found but not defined
        on the class, it raises a RuntimeError. If there are any decorators specified
        for the action, they are applied to the handler method.

        Args:
            **kwargs: Arbitrary keyword arguments that are passed to the handler method.

        Returns:
            ResponseReturnValue: The response from the handler method.

        Raises:
            RuntimeError: If the action is not defined on the class.

        """
        method = request.method.lower()
        action = self.method_actions.get(method)

        if action is None and method == "head":
            action = self.method_actions.get("get")

        if action is None:
            abort(405)

        func: RouteCallable | None = getattr(self, action, None)

        if func is None:
            msg = f"{action} not defined on {self.__class__.__name__}"
            raise RuntimeError(msg)

        if action in self.action_decorators:
            for decorator in self.action_decorators[action]:
                func = decorator(func)

        return current_app.ensure_sync(func)(**kwargs)

    @classmethod
    def as_view(
        cls,
        method_actions: dict[str, str],
        *class_args: Any,
        name: str | None = None,
        **class_kwargs: Any,
    ) -> RouteCallable:
        cls.methods = {*method_actions.keys()}
        if "get" in method_actions:
            cls.methods.add("head")
        name = name or f"{cls.__name__}: {method_actions.keys()}"
        return super().as_view(name, method_actions, *class_args, **class_kwargs)


class ModelViewSet[M: Model](ViewSet, metaclass=ABCMeta):
    """A viewset that provides default implementations for model CRUD operations."""

    model: type[M]  # ClassVar[type[M]]
    schema_cls: (
        Callable[[], ModelSchema[M]] | type[ModelSchema[M]]
    )  # ClassVar[type[ModelSchema[M]]]
    db: SQLAlchemy

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
