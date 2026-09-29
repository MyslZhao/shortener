"""
短链映射实现，包含
1. Url 映射表定义
2. MapService 数据操作类
"""

from datetime import datetime
from sqlalchemy import Integer, String, Engine, DateTime
from sqlalchemy.orm import DeclarativeBase, sessionmaker, mapped_column, Mapped


class Url(DeclarativeBase):
    """User 表
    """

    __tablename__ = 'url'
    id : Mapped[int] = mapped_column(Integer, primary_key=True)
    original_url : Mapped[str] = mapped_column(String)
    code : Mapped[str] = mapped_column(String)
    create_at : Mapped[datetime] = mapped_column(DateTime)
    expires_at : Mapped[datetime] = mapped_column(DateTime)
    version_id : Mapped[int] = mapped_column(Integer, nullable=False)

    __mapper_args__ = {"version_id_col" : version_id}

    def __repr__(self):
        return f"<Url(original_url='{self.original_url}', code='{self.code}')>"

class MapService:
    """数据库操作类
    """

    engine : Engine
    session_factory : sessionmaker

    def __init__(self, engine : Engine) :
        self.engine = engine
        self.session_factory = sessionmaker(engine)

    def __generate(self, raw : str) :
        """自动生成短链

        Args:
            raw (str): 原网址
        """
        ...

    def add(self, raw : str, expire_time : int) -> bool:
        """新增记录

        Args:
            raw (str): 原网址

        Returns:
            bool: 是否成功
        """
        ...

    def get(self, code : str) -> int:
        """查询网址

        Args:
            code (str): 对应短链

        Returns:
            int: 状态码
        """
        ...

    def remove(self, code : str) -> int:
        """移除记录

        Args:
            code (str): 短链

        Returns:
            int: 状态码
        """
        ...

    def patch(self, code : str, new_url : str, new_expire_in : int) -> int:
        """更改记录

        Args:
            code (str): 短链
            new_url (str): 新的网址
            new_expire_in (int): 新的国企时间

        Returns:
            int: 状态码
        """
        ...

