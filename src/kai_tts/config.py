from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings

from src.kai_tts.utils.custom_types import LogLevel, NetworkProtocol


class SystemConfig(BaseModel):
    log_level: LogLevel = LogLevel.INFO


class NetworkConfig(BaseModel):
    protocol: NetworkProtocol = NetworkProtocol.TCP
    port_in: int = 5555
    port_out: int = 5556


class GlobalConfig(BaseSettings):
    model_config = ConfigDict(frozen=True)
    system: SystemConfig = SystemConfig()
    network: NetworkConfig = NetworkConfig()


settings = GlobalConfig()
