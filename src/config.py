"""
环境配置类
"""

from tomllib import load
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen = True)
class ConfigProfile:
    """环境配置 Profile 类
    """
    database_url: str
    redis_host: str
    redis_port: int
    redis_db: int

def load_config(profile: str) -> ConfigProfile:
    """加载特定的环境配置

    Args:
        profile (str): 配置名

    Raises:
        SystemExit: 未知的环境配置

    Returns:
        ConfigProfile: 对应的配置 Profile 对象
    """
    config_path = Path(__file__).resolve().parent.parent / "config.toml"
    with config_path.open("rb") as f:
        data = load(f)

    if profile not in data:
        raise SystemExit(f"Unkonwn profile: {profile!r} (available: {list(data)})")

    return ConfigProfile(**data[profile])