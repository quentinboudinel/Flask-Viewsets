"""Module providing the `ViewSets` extension for Flask applications.

It allows for the integration of viewsets and model viewsets.

Classes:
    ViewSetsConfig (TypedDict): Configuration dictionary for the ViewSets extension.
    ViewSets: A class to manage and initialize view sets for a Flask application.
"""

from __future__ import annotations

from importlib.util import find_spec
from typing import TYPE_CHECKING, TypedDict

from .viewsets import ViewSet

if TYPE_CHECKING:
    from typing import NotRequired

    from flask import Flask

    from .masqla.viewsets import AbstractBaseModelViewSet
    from .typing import Model, Schema


class ViewSetsConfig(TypedDict):
    """A TypedDict for configuring view sets.

    Attributes:
        max_limit (int | None): An optional attribute that specifies the maximum limit
            for the view sets.

    """

    max_limit: NotRequired[int]


class ViewSets:
    """A class to manage and initialize view sets for a Flask application.

    :ivar config: Configuration for the view sets.
    :vartype config: ViewSetsConfig
    :ivar ModelViewSet: The model view set class, if available.
    :vartype ModelViewSet: type[ModelViewSet[Model, Schema]] | None

    :param app: The Flask application instance. If provided, the extension will be
        initialized with this app.
    :type app: Flask | None
    :param view_set_cls: The class to be used for view sets. Defaults to `ViewSet`.
    :type view_set_cls: type[ViewSet]
    :param base_model_view_set: The class to be used for model view sets. Defaults to
        `None`.
    :type base_model_view_set: type[ModelViewSet[Model, Schema]] | None

    :raises ValueError: If the configuration is invalid.

    :example:
    >>> viewsets = ViewSets(app)
    >>> viewsets.init_app(app)
    """

    ModelViewSet: type[AbstractBaseModelViewSet[Model, Schema]] | None = None

    def __init__(
        self,
        app: Flask | None = None,
        view_set_cls: type[ViewSet] = ViewSet,
        base_model_view_set: type[AbstractBaseModelViewSet] | None = None,  # type: ignore[todo]
        # TODO(quentinboudinel): Fix base_model_view_set type
        # TD-1
        config: ViewSetsConfig | None = None,
    ) -> None:
        """Initialize the extension.

        :param app: The Flask application instance. If provided, the
            extension will be initialized with this app.
        :type app: Flask | None
        :param view_set_cls: The class to be used for view sets. Defaults
            to `ViewSet`.
        :type view_set_cls: type[ViewSet]
        :param base_model_view_set: The class to be used for model view sets. Defaults
            to `None`.
        :type base_model_view_set: type[ModelViewSet[Model, Schema]] | None
        :param config: Configuration for the view sets. Defaults to `None`.
        :type config: ViewSetsConfig | None
        """
        self.config: ViewSetsConfig = config or {}
        self.view_set_cls = view_set_cls
        self.base_model_view_set = base_model_view_set  # type: ignore[todo]
        # TODO(quentinboudinel): TD-1
        # TD-1
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize the Flask application with the viewsets extension.

        This method configures the Flask application to use the viewsets extension.
        It sets up the necessary configurations and checks for the presence of
        required dependencies such as `flask_sqlalchemy`, `marshmallow_sqlalchemy`,
        and `flask_marshmallow`. If any of these dependencies are missing, the
        method returns early.

        :param app: The Flask application instance to initialize.
        :type app: Flask
        """
        self.config = app.config.get("VIEWSETS", {})  # type: ignore[assignment]
        app.extensions["viewsets"] = self
        self.ViewSet = self.view_set_cls

        if find_spec("flask_sqlalchemy") is None:
            return

        if find_spec("marshmallow_sqlalchemy") is None:
            return

        if find_spec("flask_marshmallow") is None:
            return

        if "sqlalchemy" not in app.extensions:
            return

        if "flask-marshmallow" not in app.extensions:
            return

        from .masqla.viewsets import AbstractBaseModelViewSet

        base_model_view_set = self.base_model_view_set or AbstractBaseModelViewSet  # type: ignore[todo]
        # TODO(quentinboudinel): TD-1
        # TD-1

        class ModelViewSet[M: Model, S: Schema](base_model_view_set[M, S]):  # type: ignore[todo]
            # TODO(quentinboudinel): TD-1
            # TD-1
            db = app.extensions["sqlalchemy"]
            vs = self

        self.ModelViewSet = ModelViewSet
