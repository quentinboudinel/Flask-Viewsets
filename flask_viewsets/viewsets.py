from abc import ABCMeta
from typing import Any

from flask import abort, request, current_app
from flask.views import View
from flask.typing import ResponseReturnValue, RouteCallable

from .typing import ConverterType


class ViewSet(View, metaclass=ABCMeta):
    def __init__(
        self, method_actions: dict[str, str], *args: Any, **kwargs: Any
    ) -> None:
        super().__init__()
        self.method_actions = method_actions

    def dispatch_request(self, **kwargs: ConverterType) -> ResponseReturnValue:
        method = request.method.lower()
        action = self.method_actions.get(method)

        if action is None and method == "head":
            action = self.method_actions.get("get")

        if action is None:
            abort(405)

        func = getattr(self, action, None)

        if func is None:
            raise RuntimeError(f"{action} not defined on {self.__class__.__name__}")

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
        name = (
            name
            or f"{cls.__name__}: [{', '.join(f'{method.upper()}->{action}' for method, action in method_actions.items())}]"
        )
        return super().as_view(name, method_actions, *class_args, **class_kwargs)
