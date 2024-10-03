"""ViewSets is an extension for Flask that provides a way to manage view sets."""

from __future__ import annotations

import warnings
from importlib.util import find_spec
from typing import TYPE_CHECKING, TypedDict

from flask import Flask

from .viewsets import ModelViewSet, ViewSet

if TYPE_CHECKING:
    from typing import NotRequired

    from flask import Flask
    from flask_marshmallow import Marshmallow
    from flask_sqlalchemy import SQLAlchemy

    from .typing import Model


class ViewSetsConfig(TypedDict):  # noqa: D101
    max_limit: NotRequired[int]


class ViewSets[VST: ViewSet, MVST: ModelViewSet]:
    """ViewSets is an extension for Flask that provides a way to manage view sets.

    Attributes:
        config (ViewSetsConfig): Configuration for the ViewSets extension.
        view_set_cls (type[VST]): The class to use for view sets.
        model_view_set_cls (type[MVST]): The class to use for model view sets.

    Methods:
        __init__(app: Flask | None = None, view_set_cls: type[VST] = ViewSet, model_view_set_cls: type[MVST] = ModelViewSet, config: ViewSetsConfig | None = None) -> None:
            Initializes the ViewSets extension with the given parameters.
        init_app(app: Flask) -> None:
            Initializes the Flask application with the ViewSets extension.

    """  # noqa: E501

    def __init__(
        self,
        app: Flask | None = None,
        view_set_cls: type[VST] = ViewSet,
        model_view_set_cls: type[MVST] = ModelViewSet,
        config: ViewSetsConfig | None = None,
    ) -> None:
        """Initialize the ViewSets extension with the given parameters.

        :param app: the flask app to extend, defaults to None
        :type app: Flask | None, optional
        :param view_set_cls: a base viewset class, defaults to ViewSet
        :type view_set_cls: type[VST], optional
        :param model_view_set_cls: a base model viewset class, defaults to ModelViewSet
        :type model_view_set_cls: type[MVST], optional
        :param config: some extension config, defaults to None
        :type config: ViewSetsConfig | None, optional
        """
        self.config: ViewSetsConfig = config or {}
        self.view_set_cls = view_set_cls
        self.model_view_set_cls = model_view_set_cls
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize the Flask application with the ViewSets extension.

        :param app: the flask app to extend
        :type app: Flask
        """
        self.config = app.config.get("VIEWSETS", {})  # type: ignore[partially-unknown]
        app.extensions["viewsets"] = self

        self.ViewSet = self.view_set_cls

        if find_spec("flask_sqlalchemy") is None:
            return
        if find_spec("marshmallow_sqlalchemy") is None:
            return
        if find_spec("flask_marshmallow") is None:
            return

        db_: SQLAlchemy | None = app.extensions.get("sqlalchemy")
        ma_: Marshmallow | None = app.extensions.get("flask-marshmallow")

        if db_ is None:
            msg = "SQLAlchemy extension has to be initialized before ViewSets."
            warnings.warn(msg, stacklevel=2)
            return

        if ma_ is None:
            msg = "Flask-Marshmallow extension has to be initialized before ViewSets."
            warnings.warn(msg, stacklevel=2)
            return

        class ModelViewSet[M: Model](self.model_view_set_cls):
            model: type[M]  # type: ignore[override]
            db = db_
            ma = ma_
            vs: ViewSets[VST, MVST] = self

        self.ModelViewSet = ModelViewSet
