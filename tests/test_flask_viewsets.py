import pytest
from flask import Flask

from flask_viewsets import ViewSets


@pytest.fixture
def app():
    return Flask(__name__)


def test_model_viewset(app: Flask):
    vs = ViewSets()
    vs.init_app(app)
