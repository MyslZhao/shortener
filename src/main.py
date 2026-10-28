"""
主程序入口
"""

from argparse import ArgumentParser
from config import load_config

from sqlalchemy import create_engine
from redis import Redis, ConnectionPool, exceptions as redis_exc

from cached_mapservice import CachedMapService
from mapservice import MapService, Url
from shortener import create_app

def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--profile",
        default="dev",
        help="config profile(dev/test/deploy)"
        )
    args = parser.parse_args()

    cfg = load_config(args.profile)
    print(f" * profile: {args.profile}, db: {cfg.database_url}")

    engine = create_engine(cfg.database_url)
    Url.metadata.create_all(engine)

    pool = ConnectionPool(
        host = cfg.redis_host, port = cfg.redis_port, db = cfg.redis_db,
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
    app.run(threaded=True)

if __name__ == "__main__":
    main()
