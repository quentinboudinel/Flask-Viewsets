from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

import pytest
from flask import Flask

from flask_viewsets.viewsets import ViewSet

if TYPE_CHECKING:
    from collections.abc import Iterable

    from flask.testing import FlaskClient
    from flask.typing import ResponseReturnValue, RouteCallable

    from flask_viewsets.typing import RouteDecorator


@pytest.fixture
def app() -> Flask:
    app = Flask(__name__)
    app.config.update(  # type: ignore[partially-unknown]
        {
            "TESTING": True,
        },
    )

    def decorator(_: RouteCallable) -> RouteCallable:
        def decorated(*__: Any, **___: Any) -> ResponseReturnValue:  # noqa: ANN401
            return {}, 200

        return decorated

    class TestViewSet(ViewSet):
        action_decorators: ClassVar[dict[str, Iterable[RouteDecorator]]] = {
            "to_be_decorated": (lambda f: f, decorator),
        }

        def create(self) -> ResponseReturnValue:
            return {"id": 0}, 201

        def list(self) -> ResponseReturnValue:
            return [{"id": 0}], 200

        def retrieve(self, id_: int) -> ResponseReturnValue:
            return {"id": id_}, 200

        def update(self, id_: int) -> ResponseReturnValue:
            return {"id": id_}, 200

        def partial_update(self, id_: int) -> ResponseReturnValue:
            return {"id": id_}, 200

        def destroy(self, id_: int) -> ResponseReturnValue:  # noqa: ARG002
            return b"", 204

        def to_be_decorated(self) -> ResponseReturnValue:
            msg = "This needs to be decorated."
            raise NotImplementedError(msg)

    app.add_url_rule(
        "/",
        view_func=TestViewSet.as_view(
            {
                "post": "create",
                "get": "list",
            },
        ),
    )
    app.add_url_rule(
        "/<int:id_>",
        view_func=TestViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            },
        ),
    )
    app.add_url_rule(
        "/to_be_decorated",
        view_func=TestViewSet.as_view(
            {
                "get": "to_be_decorated",
            },
        ),
    )

    return app


@pytest.fixture
def client(app: Flask):
    return app.test_client()


@pytest.fixture
def runner(app: Flask):
    return app.test_cli_runner()


def test_add_viewset(client: FlaskClient):
    response = client.post("/")
    assert response.status_code == 201
    response = client.get("/")
    assert response.status_code == 200
    response = client.get("/0")
    assert response.status_code == 200
    response = client.patch("/0")
    assert response.status_code == 200
    response = client.delete("/0")
    assert response.status_code == 204
    response = client.trace("/")
    assert response.status_code == 405
    response = client.get("/to_be_decorated")
    assert response.status_code == 200
