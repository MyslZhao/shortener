"""
短链映射实现，包含
1. Url 映射表定义
2. MapService 数据操作类
"""

from enum import Enum, auto
from datetime import datetime, timedelta
from typing import Union, Tuple
from sqlalchemy import Integer, String, Engine, DateTime
from sqlalchemy.orm import (DeclarativeBase, sessionmaker,
                            mapped_column, Mapped, Session)
from sqlalchemy.exc import IntegrityError, NoResultFound
from base62 import encode
from xxhash import xxh3_64_intdigest

class Base(DeclarativeBase):
    """
    ORM 基类

    """
    pass

class Url(Base):
    """User 表
    """

    __tablename__ = 'url'
    id : Mapped[int] = mapped_column(Integer, primary_key=True)
    url : Mapped[str] = mapped_column(String(50), unique = True)
    code : Mapped[str] = mapped_column(String, unique = True)
    create_at : Mapped[datetime] = mapped_column(DateTime)
    expires_at : Mapped[datetime] = mapped_column(DateTime)
    #version_id : Mapped[int] = mapped_column(Integer, nullable=False)

    #__mapper_args__ = {"version_id_col" : version_id}

    def __repr__(self):
        return ("<Url(" +
            f"id='{self.id}'," +
            f"url='{self.url}'," +
            f"code='{self.code}'," +
            f"create_at='{self.create_at}'," +
            f"expires_at='{self.expires_at}')>")

class MapService:
    """
    数据库操作类

    """
    class NoneType(Enum):
        """
        None状态枚举

        """
        UNKNOWN = auto()
        EXPIRED = auto()

    engine : Engine
    session_factory : sessionmaker[Session] # pylint: disable=unsubscriptable-object

    def __init__(self, engine : Engine) :
        self.engine = engine
        self.session_factory = sessionmaker[Session](engine) # pylint: disable=unsubscriptable-object

    def __generate(self, raw : str) -> str :
        """自动生成短链源链

        Args:
            raw (str): 原网址
        """
        semi = encode(xxh3_64_intdigest(raw.encode()))
        return semi

    def add(self, raw : str, expire_time : int) -> Tuple[bool, str]:
        """新增记录

        Args:
            raw (str): 原网址

        Returns:
            Tuple[bool, str]: 是否发生创建, 短链
        """
        with self.session_factory() as session:
            try:
                if (len(raw) > 50) :
                    return (False, "")
                exist = (session.query(Url)
                         .filter(Url.url == raw)
                         .one_or_none())
                if exist:
                    return (False, exist.code)

                short_source = self.__generate(raw)
                i = 0

                # 若碰撞则位移
                while (session.query(Url)
                 .filter(Url.code == short_source[i:i + 6])
                 .one_or_none()):
                    if short_source[i + 7]:
                        i += 1
                    else :
                        raise IndexError
                session.add(Url(
                    url = raw,
                    code = short_source[i:i + 6],
                    create_at = datetime.now(),
                    expires_at = (datetime.now() +
                                  timedelta(seconds=expire_time))
                ))
                session.commit()
                return (True, short_source[i:i + 6])
            except IntegrityError:
                return (False, short_source[i:i + 6])
            except IndexError:
                return (False, "")


    def get(self, code : str) -> Union[str, NoneType]:
        """查询网址

        Args:
            code (str): 对应短链

        Returns:
            Union[str, NoneType]: 原网址/ 错误状态
        """
        with self.session_factory() as session:
            try:
                result = (session.query(Url)
                    .filter(Url.code == code)
                    .one())
                if result.expires_at < datetime.now() :
                    return self.NoneType.EXPIRED
                return result.url
            except NoResultFound:
                return self.NoneType.UNKNOWN

    def remove(self, code : str) -> bool:
        """移除记录

        Args:
            code (str): 短链

        Returns:
            bool: 是否成功
        """
        with self.session_factory() as session:
            try:
                obj = (session.query(Url)
                    .filter(Url.code == code)
                    .one())
                session.delete(obj)
                session.commit()
                return True
            except NoResultFound:
                return False

    def patch(self,
              code : str,
              target : str,
              param : str | int
              ) -> Union[Tuple[str, str], NoneType]:
        """更改记录

        Args:
            code (str): 短链
            target (str): 更改项
            param (str | int): 目标值

        Returns:
            Union[Tuple[str, str], NoneType]: 新的网站和对应的短链/ 错误状态
        """
        with self.session_factory() as session:
            try:
                obj = (session.query(Url)
                       .filter(Url.code == code)
                       .one())
                if (obj.expires_at <= datetime.now()):
                    return self.NoneType.EXPIRED

                match target:
                    case "url":
                        obj.url = str(param)
                    case "expire_in":
                        obj.expires_at = datetime.now() + timedelta(seconds=int(param))
                session.commit()
                return (obj.url, code)
            except NoResultFound:
                return self.NoneType.UNKNOWN
