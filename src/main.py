"""
主程序入口
"""

from sqlalchemy import create_engine
from redis import Redis, ConnectionPool, exceptions as redis_exc

from cached_mapservice import CachedMapService
from mapservice import MapService, Url
from shortener import create_app

def main():
    engine = create_engine("sqlite:///urls.db")
    Url.metadata.create_all(engine)

    pool = ConnectionPool(
        host = "localhost", port = 6379, db = 0,
        decode_responses = True,
        max_connections = 20,
    )

    client = Redis(connection_pool = pool)
    try:
        client.ping()
        service = CachedMapService(
            inner = MapService(engine),
            client = client
            )
    except redis_exc.ConnectionError:
        print(" * Warning: Redis has no response, using default mapservice(no cache).")
        service = MapService(engine)

    app = create_app(service)
    app.run()

if __name__ == "__main__":
    main()
