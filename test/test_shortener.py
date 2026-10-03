import pytest
from typing import Any, Generator
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import create_engine
from shortener import create_app
from mapservice import MapService, Url

@pytest.fixture
def app() -> Flask:
    engine = create_engine("sqlite:///:memory:")
    Url.metadata.create_all(engine)
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

def test_create_and_get(client : FlaskClient, raw_urls : list[str]):
    for url in raw_urls:
        resp = client.post("/short", json = {
            "url": url,
            "expire_in": 600
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert url == data["url"]
        resp = client.get(f"/{data['code']}")
        assert resp.status_code == 302
        assert resp.headers["Location"] == url

def test_repeat_create(client : FlaskClient):
    url = "https://www.gov.cn"
    resp = client.post("/short", json = {
        "url": url,
        "expire_in": 600
    })
    assert resp.status_code == 201
    short : str = resp.get_json()["code"]
    resp = client.post("/short", json = {
        "url": url,
        "expire_in": 600
    })
    assert resp.status_code == 200
    new_short : str = resp.get_json()["code"]
    assert short == new_short