# pylint: skip-file
import pytest
from typing import Any, Generator
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import create_engine
from json import loads
from shortener import create_app
from mapservice import MapService

@pytest.fixture
def app() -> Flask:
    engine = create_engine("sqlite:///:memory:")
    service = MapService(engine)
    app = create_app(service)
    app.config.update({"TESTING": True})
    return app

@pytest.fixture
def client(app : Flask) -> Generator[FlaskClient, Any, None]:
    with app.test_client() as tester:
        yield tester

@pytest.fixture
def raw_urls() -> list[str]:
    return [
        "https://www.baidu.com",
        "https://steamfu.com",
        "https://github.com",
        "https://www.bing.cn",
    ]

def test_create(client : FlaskClient, raw_urls : list[str]):
    for url in raw_urls:
        resp = client.post("/short", json = {
            "url": url,
            "expire_in": 600
        })
        data = resp.get_json()
        assert resp.status_code == 201
        assert url in data

def test_repeat_create(client : FlaskClient):
    url = "https://www.gov.cn"
    resp = client.post("/short", json = {
        "url": url,
        "expire_in": 600
    })
    short : str = loads(resp.get_json())["code"]
    assert resp.status_code == 201
    resp = client.post("/short", json = {
        "url": url,
        "expire_in": 600
    })
    new_short : str = loads(resp.get_json())["code"]
    assert resp.status_code == 200
    assert short == new_short