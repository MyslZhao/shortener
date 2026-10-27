"""
装饰器类:

通过外部redis缓存增强原 MapService 类
"""

from typing import Union, Tuple

from redis import Redis, ConnectionPool

from mapservice import MapService
from status import Status, GetResult

class CachedMapService:
    """
    redis 缓存增强类
    """

    __sql : MapService

    __redis : Redis

    def __init__(self, inner : MapService, client : Redis ):
        self.__sql = inner
        self.__redis = client

    @staticmethod
    def __key(code: str) -> str:
        return f"short:{code}"

    def add(self, raw : str, expire_time : int) -> Tuple[bool, str]:
        """新增记录,
        逻辑基本与原 MapService 一致

        Args:
            raw (str): 原网址
            expire_time (int): 有效期

        Returns:
            Tuple[bool, str]: 是否新建条目，短链
        """
        return self.__sql.add(raw, expire_time)

    def get(self, code : str) -> GetResult:
        """获取记录，
        先行查询 redis 缓存，
        miss 则再查询 sql 并回填

        Args:
            code (str): 目标短链

        Returns:
            GetResult: 结果闭包
        """
        res = self.__redis.get(self.__key(code))
        if res is not None:
            if not isinstance(res, str):
                raise TypeError(
                    "Undecode message, please set 'decode_responses=True'."
                )
            return GetResult(
                status=Status.SUCCESS,
                url=res,
                ttl=None
            )

        res = self.__sql.get(code)
        if res.status is not Status.SUCCESS:
            return res

        if res.ttl is not None and res.ttl > 0 and res.url:
            self.__redis.setex(self.__key(code), res.ttl, res.url)

        return res

    def remove(self, code : str) -> bool:
        """移除短链，
        同时移除 redis 缓存记录

        Args:
            code (str): 目标短链

        Returns:
            bool: 操作是否成功
        """
        ok = self.__sql.remove(code)
        if ok:
            self.__redis.delete(self.__key(code))

        return ok


    def patch(self,
              code : str,
              new_expire_in : int
              ) -> Status:
        """延期/提前到期，
        同时修改 redis 缓存记录

        Args:
            code (str): 目标短链
            new_expire_in (int): 新的有效时间

        Returns:
            Status: 操作状态
        """

        ok = self.__sql.patch(code, new_expire_in)
        if ok is Status.SUCCESS:
            self.__redis.expire(self.__key(code), new_expire_in)

        return ok
