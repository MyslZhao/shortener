#pylint: skip-file
import pytest
from time import sleep
from sqlalchemy import create_engine
from mapservice import MapService, Url

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

def test_add_and_get(service : MapService, raw_urls : list[str]):
    for url in raw_urls:
        code = service.add(url, 600)
        assert code[0]
        assert service.get(code[1]) == url

def test_repeat_add(service : MapService):
    url = "https://www.baidu.com"
    code1 = service.add(url, 600)
    code2 = service.add(url, 600)
    assert not code2[0]
    assert code1[1] == code2[1]

def test_patch_url_and_get(service : MapService):
    code = service.add("https://github.com", 600)
    result = service.patch(code[1], "https://gitlab.com", 600)
    assert result == ("https://gitlab.com", code[1])
    assert service.get(code[1]) == "https://gitlab.com"

def test_patch_expired_and_get(service : MapService):
    code = service.add("https://www.mozilla.org", 1)
    sleep(2)
    assert service.get(code[1]) == MapService.NoneType.EXPIRED
    service.patch(code[1], "https://www.mozilla.org", 600)
    assert service.get(code[1]) == "https://www.mozilla.org"

def test_remove_and_get(service : MapService):
    code = service.add("https://github.com", 600)
    assert service.remove(code[1]) is True
    assert service.get(code[1]) == MapService.NoneType.UNKNOWN
    assert service.remove(code[1]) is False

def test_expired_and_get(service : MapService):
    code = service.add("https://github.com", 1)
    sleep(2)
    assert service.get(code[1]) == MapService.NoneType.EXPIRED

def test_get_unknown_code(service : MapService):
    assert service.get("not_exist") == MapService.NoneType.UNKNOWN

def test_patch_unknown_code(service : MapService):
    assert service.patch("not_exist", "https://x.com", 600) == MapService.NoneType.UNKNOWN