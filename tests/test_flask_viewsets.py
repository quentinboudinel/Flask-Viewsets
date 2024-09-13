import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask.typing import ResponseReturnValue

from flask_viewsets import ViewSet


@pytest.fixture()
def app():
    app = Flask(__name__)
    app.config.update({  # type: ignore
        "TESTING": True,
    })

    class TestViewSet(ViewSet):
        def create(self) -> ResponseReturnValue:
            return {"id": 0}, 201

        def list(self) -> ResponseReturnValue:
            return [{"id": 0}], 200

        def retrieve(self, id: int) -> ResponseReturnValue:
            return {"id": id}, 200

        def update(self, id: int) -> ResponseReturnValue:
            return {"id": id}, 200

        def partial_update(self, id: int) -> ResponseReturnValue:
            return {"id": id}, 200

        def destroy(self, id: int) -> ResponseReturnValue:
            return b"", 204

    app.add_url_rule(
        "/",
        view_func=TestViewSet.as_view({
            "post": "create",
            "get": "list",
        }),
    )
    app.add_url_rule(
        "/<int:id>",
        view_func=TestViewSet.as_view({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
    )

    yield app


@pytest.fixture()
def client(app: Flask):
    return app.test_client()


@pytest.fixture()
def runner(app: Flask):
    return app.test_cli_runner()


def test_add_viewset(app: Flask, client: FlaskClient):
    print(app.url_map)

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
