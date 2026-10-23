"""
装饰器类:

通过外部redis缓存增强原 MapService 类
"""

from typing import Union, Tuple
from redis import Redis, ConnectionPool
from mapservice import MapService

class CachedMapService:
    """
    redis 缓存增强类
    """

    __sql : MapService

    __redis : Redis

    def __init__(self, engine : MapService, redis : Redis ):
        self.__sql = engine
        self.__redis = redis

    def add(self, raw : str, expire_time : int) -> Tuple[bool, str]:
        """新增记录,
        逻辑基本与原 MapService 一致

        Args:
            raw (str): _description_
            expire_time (int): _description_

        Returns:
            Tuple[bool, str]: _description_
        """
        ...

    def get(self, code : str) -> Union[str, NoneType]:
        ...

    def remove(self, code : str) -> bool:
        ...


    def patch(self,
              code : str,
              new_expire_in : int
              ) -> Union[None, NoneType]:
        ...
