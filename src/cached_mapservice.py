"""
装饰器类:  

通过外部redis缓存增强原 MapService 类
"""

from redis import Redis
from mapservice import MapService

class CachedMapService:
    """
    redis 缓存增强类
    """

    __service : MapService

    def CachedMapService(self, origin : MapService):
        self.__service = origin

