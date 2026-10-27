"""
状态类
"""

from enum import Enum, auto
from typing import NamedTuple

class Status(Enum):
    """
    操作状态枚举

    """
    UNKNOWN = auto()
    EXPIRED = auto()
    SUCCESS = auto()

class GetResult(NamedTuple):
    """
    get 结果闭包

    包含操作状态，原网址和延迟
    """
    status : Status
    url : str | None = None
    ttl : int | None = None