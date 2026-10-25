import pytest
from fakeredis import FakeRedis
from sqlalchemy import create_engine, Engine

from mapservice import MapService, Url
from status import Status
from cached_mapservice import CachedMapService

@pytest.fixture
def inner() -> MapService:
    engine = create_engine("sqlite:///:memory:")
    Url.metadata.create_all(engine)
    return MapService(engine)

@pytest.fixture
def redis_client() -> FakeRedis:
    return FakeRedis(decode_responses = True)

@pytest.fixture
def service(inner : MapService, redis_client : FakeRedis):
    return CachedMapService(inner, redis_client)

def test_gei_hit_skips_db(service : CachedMapService,
                          inner : MapService,
                          monkeypatch : pytest.MonkeyPatch):
    """测试缓存命中时是否跳过数据库查询"""
    _, code = service.add("https://x.com", 600)
    service.get(code)

    def gotcha(code):
        raise AssertionError(f'缓存命中，但 DB 仍然被查询, 值为 {code!r}')

    monkeypatch.setattr(inner, "get", gotcha)

    res = service.get(code)
    assert res.status == Status.SUCCESS
    assert res.url == "https://x.com"

def test_get_miss_populates_cache(service : CachedMapService, redis_client : FakeRedis):
    """测试缓存填入"""
    # 即缓存回填，直到短码第一次被 get 时才录入缓存
    _, code = service.add("https://x.com", 600)
    assert redis_client.get(f"short:{code}") is None

    service.get(code)
    assert redis_client.get(f"short:{code}") == "https://x.com"

def test_expired_remove(service : CachedMapService, redis_client : FakeRedis):
    """过期短链移除"""
    # TTL在几十到几百毫秒，考虑到项目规模，处于允许范围内
    _, code = service.add("https://x.com", -1)

    res = service.get(code)
    assert res.status == Status.EXPIRED
    assert redis_client.get(f"short:{code}") is None

def test_remove_clears_cache(service : CachedMapService, redis_client : FakeRedis):
    """delete 缓存同步清理"""
    _, code = service.add("https://x.com", 600)
    service.get(code)
    service.remove(code)
    assert redis_client.get(f"short:{code}") is None

def test_patch_shortens_ttl_no_stale(service, redis_client):
    """patch 提前到期缓存同步"""
    # 允许 1s 以下的 ttl
    _, code = service.add("https://x.com", 600)
    service.get(code)
    service.patch(code, 1)
    ttl = redis_client.ttl(f"short:{code}")
    assert 0 <= ttl <= 1

def test_patch_extends_ttl(service, redis_client):
    """patch 延期缓存同步"""
    _, code = service.add("https://x.com", 10)
    service.get(code)
    service.patch(code, 600)
    assert redis_client.ttl(f"short:{code}") > 500
