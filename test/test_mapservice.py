from time import sleep
import pytest
from sqlalchemy import create_engine
from src.mapservice import MapService, Url

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

def test_add_returns_created_flag(service):
    created, code = service.add("https://github.com", 600)
    assert created is True

def test_repeat_add_returns_same_code(service):
    _, code1 = service.add("https://github.com", 600)
    created, code2 = service.add("https://github.com", 600)
    assert created is False
    assert code1 == code2

def test_get_unknown_returns_unknown(service):
    assert service.get("not_exist") == MapService.NoneType.UNKNOWN

def test_get_expired_returns_expired(service):
    _, code = service.add("https://github.com", -1)
    assert service.get(code) == MapService.NoneType.EXPIRED

def test_remove_twice(service):
    _, code = service.add("https://github.com", 600)
    assert service.remove(code) is True
    assert service.remove(code) is False

def test_patch_unknown_returns_unknown(service):
    assert service.patch("not_exist", "https://x.com", 600) == MapService.NoneType.UNKNOWN