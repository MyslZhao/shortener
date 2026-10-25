import pytest
from freezegun import freeze_time
from sqlalchemy import create_engine

from mapservice import MapService, Url
from status import Status

@pytest.fixture
def service() -> MapService:
    engine = create_engine("sqlite:///:memory:")
    Url.metadata.create_all(engine)
    return MapService(engine)

@pytest.fixture
def raw_urls() -> list[str]:
    return [
        "https://www.baidu.com",
        "https://steamfu.com",
        "https://github.com",
        "https://www.bing.cn",
    ]

def test_add_returns_created_flag(service : MapService):
    created = service.add("https://github.com", 600)[0]
    assert created is True

def test_repeat_add_returns_same_code(service : MapService):
    _, code1 = service.add("https://github.com", 600)
    created, code2 = service.add("https://github.com", 600)
    assert created is False
    assert code1 == code2

def test_get_unknown_returns_unknown(service : MapService):
    assert service.get("udv5ye").status == Status.UNKNOWN

def test_get_expired_returns_expired(service : MapService):
    _, code = service.add("https://github.com", -1)
    res = service.get(code)
    assert res.status == Status.EXPIRED
    assert not res.url

def test_remove_twice(service : MapService):
    _, code = service.add("https://github.com", 600)
    assert service.remove(code) is True
    assert service.remove(code) is False

def test_patch_expired_returns_expired(service : MapService):
    with freeze_time("2026-01-01 00:00:00") as frozen:
        _, code = service.add("https://github.com", 1)
        frozen.tick(2)
        assert service.patch(code, 600) == Status.EXPIRED

def test_patch_expire_longer_then_get(service : MapService):
    with freeze_time("2026-01-01 00:00:00") as frozen:
        _, code = service.add("https://github.com", 5)
        service.patch(code, 600)
        frozen.tick(5)
        res = service.get(code)
        assert res.status == Status.SUCCESS
        assert res.url == "https://github.com"
