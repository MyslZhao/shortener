from typing import Any, Generator, Tuple
from time import sleep
import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import create_engine
from shortener import create_app
from mapservice import MapService, Url

@pytest.fixture
def service() -> MapService:
    engine = create_engine("sqlite:///:memory:")
    Url.metadata.create_all(engine)
    service = MapService(engine)
    return service

@pytest.fixture
def app(service : MapService) -> Flask:
    app = create_app(service)
    app.config.update({"TESTING": True})
    return app

@pytest.fixture
def client(app : Flask) -> Generator[FlaskClient, Any, None]:
    with app.test_client() as tester:
        yield tester

@pytest.fixture
def inner_create(service : MapService):
    def _inner_create(url : str, expire_in : int = 600) -> str:
        created, short = service.add(url, expire_in)
        assert created, f"Generate Failed For {url}"
        return short
    return _inner_create

@pytest.fixture
def outter_create(client : FlaskClient):
    def _outter_create(url : str, expire_in : int = 600) -> str:
        resp = client.post("/short", json = {
            "url": url,
            "expire_in": expire_in
        })
        assert resp.status_code == 201
        return resp.get_json()["code"]
    return _outter_create

def test_create(client : FlaskClient):
    url = "https://www.baidu.com"
    resp = client.post("/short", json = {
        "url": url,
        "expire_in": 600
    })
    assert resp.status_code == 201
    assert resp.get_json()["url"] == url
    assert resp.get_json()["code"]

def test_repeat_create(client : FlaskClient):
    url = "https://cn.bing.com"
    resp = client.post("/short", json = {
        "url": url,
        "expire_in": 600
    })
    assert resp.status_code == 201
    code = resp.get_json()["code"]
    new_resp = client.post("/short", json = {
        "url": url,
        "expire_in": 600
    })
    assert new_resp.status_code == 200
    assert code == new_resp.get_json()["code"]

def test_missing_param_create(client : FlaskClient):
    no_url_resp = client.post("/short", json = {
        "expire_in": 600
    })
    assert no_url_resp.status_code == 400
    no_expired_resp = client.post("/short", json = {
        "url": "https://github.com"
    })
    assert no_expired_resp.status_code == 400

def test_illegal_json_create(client : FlaskClient):
    resp = client.post("/short", json = {
        "cat": "oiiai",
        "spin": True
    })
    assert resp.status_code == 400

def test_not_json_create(client : FlaskClient):
    data_resp = client.post("/short", data = {
        "url": "https://github.com",
        "expire_in": 600
    })
    assert data_resp.status_code == 400

    xml_resp = client.post("/short", data = """<?xml version='1.0'?>""",
                           content_type = "application/xml")
    assert xml_resp.status_code == 400

def test_abnormal_param_create(client : FlaskClient):
    abnormal_url = "oiiai oiiaii"
    abnormal_url_resp = client.post("/short", json = {
        "url": abnormal_url,
        "expire_in": 600
    })
    assert abnormal_url_resp.status_code == 400

    # expire_in 要求至少为 0
    negative_expire_resp = client.post("/short", json = {
        "url": "https://spinning.cat",
        "expire_in": -10
    })
    assert negative_expire_resp.status_code == 400

    # 如果expire_in参数为浮点数，直接取整不报错

    wrong_type_resp = client.post("/short", json = {
        "url": 600,
        "expire_in": "https://minecraft.wiki"
    })
    assert wrong_type_resp.status_code == 400

def test_long_url_create(client : FlaskClient):
    """
    长度超限url测试
    """
    url = ("https://www.sbbcsiubvf.com/uirbchbdsvibesvdbzvibzhbvu" +
           "irbiubcdlcbzvhbiabweifbvivawcvewbaibcvyirawuiefbviabfiqlceC")
    resp = client.post("/short", json = {
        "url": url,
        "expire_in": 600
    })
    assert resp.status_code == 400

def test_create_then_get(client : FlaskClient, inner_create):
    """
    正常 get 测试
    """
    url = "https://www.baidu.com"
    code = inner_create(url, 600)
    resp = client.get(f"/{code}")
    assert resp.status_code == 302
    assert resp.headers.get("Location") == url

def test_unknown_code_get(client : FlaskClient):
    """
    不存在的 code get 测试
    """
    unknown_code = "h38fva"
    resp = client.get(f"/{unknown_code}")
    assert resp.status_code == 404

def test_expired_code_get(client : FlaskClient, inner_create):
    """
    过期 code get 测试
    """
    code = inner_create("https://github.com", 1)
    sleep(2)
    new_resp = client.get(f"/{code}")
    assert new_resp.status_code == 410


def test_create_then_delete_then_get(client : FlaskClient):
    """
    正常 delete 测试
    """
    url = "https://www.mozilla.org/en-US/"
    resp = client.post("/short", json = {
        "url": url,
        "expire_in": 600
    })
    assert resp.status_code == 201
    code = resp.get_json()["code"]

    delete_resp = client.delete(f"/{code}")
    assert delete_resp.status_code == 204

    get_resp = client.get(f"/{code}")
    assert get_resp.status_code == 404

def test_create_then_repeat_delete(client : FlaskClient):
    """
    重复 delete 测试
    """
    url = "https://docs.python.org"
    resp = client.post("/short", json = {
        "url": url,
        "expire_in": 600
    })
    assert resp.status_code == 201
    code = resp.get_json()["code"]

    delete_resp = client.delete(f"/{code}")
    assert delete_resp.status_code == 204
    redelete_resp = client.delete(f"/{code}")
    assert redelete_resp.status_code == 404

def test_unknown_code_delete(client : FlaskClient):
    """
    未知 code delete 测试
    """
    code = "kcyq83"
    resp = client.delete(f"/{code}")
    assert resp.status_code == 404

def test_create_then_patch_url_then_get(client : FlaskClient):
    """
    正常 patch url 测试
    """
    # 新的url不再重新生成一次短码，沿用该短码
    # 这可能会导致人为碰撞
    url = "https://cn.bing.com"
    new_url = "https://www.baidu.com"
    resp = client.post("/short", json = {
        "url": url,
        "expire_in": 600
    })
    assert resp.status_code == 201
    code = resp.get_json()["code"]

    patch_resp = client.patch(f"/{code}", json = {
        "url": new_url
    })
    assert patch_resp.status_code == 200
    assert patch_resp.get_json()["code"] == code
    assert patch_resp.get_json()["url"] == new_url

    get_resp = client.get(f"/{code}")
    assert get_resp.status_code == 302
    assert get_resp.headers.get("Location") == new_url

def test_renew_expire_then_get(client : FlaskClient):
    """
    正常续期 patch expire 测试
    """
    url = "https://cn.bing.com"
    resp = client.post("/short", json = {
        "url": url,
        "expire_in": 5
    })
    assert resp.status_code == 201
    code = resp.get_json()["code"]

    patch_resp = client.patch(f"/{code}", json = {
        "expire_in": 700
    })
    assert patch_resp.status_code == 200
    sleep(10)

    get_resp = client.get(f"/{code}")
    assert get_resp.status_code == 302
    assert get_resp.headers.get("Location") == url

def test_terminate_expire_then_get(client : FlaskClient):
    """
    正常终止 patch expire 测试
    """
    url = "https://cn.bing.com"
    resp = client.post("/short", json = {
        "url": url,
        "expire_in": 600
    })
    assert resp.status_code == 201
    code = resp.get_json()["code"]

    patch_resp = client.patch(f"/{code}", json = {
        "expire_in": 0
    })
    assert patch_resp.status_code == 200

    get_resp = client.get(f"/{code}")
    assert get_resp.status_code == 410

def test_collide_by_patch(client : FlaskClient):
    """
    人为 patch url 碰撞测试
    """
    url = "https://github.com"
    new_url = "https://www.mozilla.org"
    create_resp = client.post("/short", json = {
        "url": url,
        "expire_in": 600
    })
    assert create_resp.status_code == 201
    code = create_resp.get_json()["code"]
    patch_resp = client.patch(f"/{code}", json = {
        "url": new_url
    })
    assert patch_resp.status_code == 200
    recreate_resp = client.post("/short", json = {
        "url": url,
        "expire_in": 600
    })
    # 服务器通过移位避免碰撞，若避免失败则500 Internal Server Error
    assert recreate_resp.status_code == 201
    new_code = recreate_resp.get_json()["code"]
    assert code != new_code

def test_expired_patch(client : FlaskClient):
    """
    过期 code patch 测试
    """
    # 新的expire_in应在code的有效期内完成修改来实现续期或提前到期
    resp = client.post("/short", json = {
        "url": "https://www.microsoft.com/",
        "expire_in": 3
    })
    assert resp.status_code == 201
    code = resp.get_json()["code"]
    sleep(5)
    patch_resp = client.patch(f"/{code}", json = {
        "expire_in": 600
    })
    assert patch_resp.status_code == 410
    get_resp = client.get(f"/{code}")
    assert get_resp.status_code == 410

def test_empty_json_patch(client : FlaskClient, inner_create):
    """
    空 json patch 测试
    """
    code = inner_create("https://www.baidu.com", 600)
    resp = client.patch(f"/{code}", json = {})
    assert resp.status_code == 400

def test_illegal_json_patch(client : FlaskClient, inner_create):
    """
    错误结构 json patch 测试
    """
    code = inner_create("https://www.baidu.com")
    resp = client.patch(f"/{code}", json = {
        "cat": "oiiai"
    })
    assert resp.status_code == 400

def test_illegal_param_patch(client : FlaskClient, inner_create):
    """
    内部类型错误/非法数据 json patch 测试
    """
    code = inner_create("https://www.baidu.com")
    resp = client.patch(f"/{code}", json = {
        "expire_in": "hdov"
    })
    assert resp.status_code == 422

def test_unknown_code_patch(client : FlaskClient):
    """
    未知 code patch 测试
    """
    code = "w24d7g"
    resp = client.patch(f"/{code}", json = {
        "url": "https://github.com"
    })
    assert resp.status_code == 404

def test_not_json_patch(client : FlaskClient, inner_create):
    """
    非 json 数据 patch 测试
    """
    code = inner_create("https://docs.python.org", 600)
    resp = client.patch(f"/{code}", data = """<?xml version='1.0'?>""",
                           content_type = "application/xml")
    assert resp.status_code == 415
