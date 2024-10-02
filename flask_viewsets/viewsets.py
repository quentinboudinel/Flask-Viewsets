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
from typing import TYPE_CHECKING, Any, ClassVar

from flask import abort, current_app, request
from flask.views import View

if TYPE_CHECKING:
    from collections.abc import Iterable

    from flask.typing import ResponseReturnValue, RouteCallable

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
        *class_args: Any,  # noqa: ANN401
        name: str | None = None,
        **class_kwargs: Any,  # noqa: ANN401
    ) -> RouteCallable:
        """Create a view function that can be used with Flask routing.

        Args:
            cls: The class instance.
            method_actions (dict[str, str]): A dictionary mapping HTTP methods to action
                names.
            *class_args (Any): Additional positional arguments for the class.
            name (str | None, optional): The name of the view. Defaults to None.
            **class_kwargs (Any): Additional keyword arguments for the class.

        Returns:
            RouteCallable: A callable that can be used as a Flask route.

        """
        cls.methods = {*method_actions.keys()}
        if "get" in method_actions:
            cls.methods.add("head")
        name = name or f"{cls.__name__}: {method_actions.keys()}"
        return super().as_view(name, method_actions, *class_args, **class_kwargs)
