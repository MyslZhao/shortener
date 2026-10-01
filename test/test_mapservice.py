#pylint: skip-file
import pytest
from time import sleep
from sqlalchemy import create_engine
from mapservice import MapService, Url

@pytest.fixture
def service():
    engine = create_engine("sqlite:///:memory:")
    Url.metadata.create_all(engine)
    return MapService(engine)

@pytest.fixture
def raw_urls():
    return [
        "https://www.baidu.com",
        "https://steamfu.com",
        "https://github.com",
        "https://www.bing.cn",
    ]

def test_add_and_get(service, raw_urls):
    for url in raw_urls:
        code = service.add(url, 600)
        assert service.get(code) == url

def test_repeat_add(service):
    url = "https://www.baidu.com"
    code1 = service.add(url, 600)
    code2 = service.add(url, 600)
    assert code1 == code2

def test_patch_and_get(service):
    code = service.add("https://github.com", 600)
    new_code, new_url = service.patch(code, "https://gitlab.com", 600)
    assert service.get(new_code) == "https://gitlab.com"

def test_remove_and_get(service):
    code = service.add("https://github.com", 600)
    assert service.remove(code) is True
    assert service.get(code) == MapService.NoneType.UNKNOWN
    assert service.remove(code) is False

def test_expired_and_get(service):
    code = service.add("https://github.com", 1)
    sleep(2)
    assert service.get(code) == MapService.NoneType.EXPIRED

def test_get_unknown_code(service):
    assert service.get("not_exist") == MapService.NoneType.UNKNOWN

def test_patch_unknown_code(service):
    assert service.patch("not_exist", "https://x.com", 600) == MapService.NoneType.UNKNOWN