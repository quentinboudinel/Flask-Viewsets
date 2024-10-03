from __future__ import annotations

from abc import ABCMeta
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

import pytest
from flask import Flask
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy

from flask_viewsets import ViewSets
from flask_viewsets.masqla.viewsets import ModelViewSet
from flask_viewsets.typing import Model, ModelSchema

if TYPE_CHECKING:
    from flask.typing import ResponseReturnValue


@pytest.fixture
def db() -> SQLAlchemy:
    return SQLAlchemy()


@pytest.fixture
def ma() -> Marshmallow:
    return Marshmallow()


@pytest.fixture
def app(db: SQLAlchemy, ma: Marshmallow) -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    db.init_app(app)
    ma.init_app(app)
    return app


@pytest.fixture
def model(db: SQLAlchemy) -> type[Model]:
    class TestModel(db.Model):
        __tablename__ = "test"
        id = db.Column(db.Integer, primary_key=True)

    return TestModel


@pytest.fixture
def schema_cls[M: Model](ma: Marshmallow, model: type[M]) -> type[ModelSchema[M]]:
    m = model

    class TestSchema(ma.SQLAlchemyAutoSchema):
        class Meta:  # type: ignore[overriden-symbol]
            model = m

    return TestSchema


def test_model_viewset[M: Model](
    db: SQLAlchemy,
    app: Flask,
    model: type[M],
    schema_cls: type[ModelSchema[M]],
) -> None:
    vs = ViewSets[Model]()
    vs.init_app(app)

    with app.app_context():
        db.create_all()
        db.session.add(model(id=0))  # type: ignore[arg-type]
        db.session.add(model(id=1))  # type: ignore[arg-type]
        db.session.commit()

    m = model
    s = schema_cls

    assert vs.ModelViewSet is not None

    class TestViewSet(vs.ModelViewSet):
        model = m
        schema_cls = s

    app.add_url_rule(
        "/tests",
        endpoint="tests",
        view_func=TestViewSet.as_view({"get": "list"}),
    )
    app.add_url_rule(
        "/tests/<int:id>",
        endpoint="test",
        view_func=TestViewSet.as_view({"get": "retrieve"}),
    )
    client = app.test_client()
    response = client.get("/tests")
    assert response.json == [{"id": 0}, {"id": 1}]
    where = quote("id=0")
    response = client.get(f"/tests?where={where}")
    assert response.json == [{"id": 0}]
    order_by = quote("-id")
    response = client.get(f"/tests?order_by={order_by}")
    assert response.json == [{"id": 1}, {"id": 0}]
    response = client.get("/tests/0")
    assert response.json == {"id": 0}


def test_base_model_viewset[M: Model](
    app: Flask,
    db: SQLAlchemy,
    model: type[M],
    schema_cls: type[ModelSchema[M]],
) -> None:
    class MyModelViewSet[M_: Model](
        ModelViewSet[M_],
        metaclass=ABCMeta,
    ):
        def action(self, **_: Any) -> ResponseReturnValue:  # noqa: ANN401
            return {"message": "action"}, 200

    vs = ViewSets[Model](model_view_set_cls=MyModelViewSet)
    vs.init_app(app)

    with app.app_context():
        db.create_all()
        db.session.add(model(id=0))  # type: ignore[arg-type]
        db.session.add(model(id=1))  # type: ignore[arg-type]
        db.session.commit()

    m = model
    s = schema_cls

    assert vs.ModelViewSet is not None

    class TestViewSet(vs.ModelViewSet):
        model = m
        schema_cls = s

    app.add_url_rule(
        "/tests",
        endpoint="tests",
        view_func=TestViewSet.as_view({"get": "list"}),
    )
    app.add_url_rule(
        "/tests/<int:id>",
        endpoint="test",
        view_func=TestViewSet.as_view({"get": "retrieve"}),
    )
    app.add_url_rule(
        "/tests/action",
        endpoint="test-action",
        view_func=TestViewSet.as_view({"post": "action"}),
    )
    client = app.test_client()
    response = client.get("/tests")
    assert response.json == [{"id": 0}, {"id": 1}]
    where = quote("id=0")
    response = client.get(f"/tests?where={where}")
    assert response.json == [{"id": 0}]
    order_by = quote("-id")
    response = client.get(f"/tests?order_by={order_by}")
    assert response.json == [{"id": 1}, {"id": 0}]
    response = client.get("/tests/0")
    assert response.json == {"id": 0}
    response = client.post("/tests/action")
    assert response.json == {"message": "action"}
