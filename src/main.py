"""
主程序入口
"""

from sqlalchemy import create_engine
from mapservice import MapService, Url
from shortener import create_app


if __name__ == "__main__":
    engine = create_engine("sqlite:///url.db")
    Url.metadata.create_all(engine)
    service = MapService(engine)
    app = create_app(service)
    app.run()
