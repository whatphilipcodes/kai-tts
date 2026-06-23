from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings

from src.kai_tts.utils.custom_types import LogLevel, NetworkProtocol


class SystemConfig(BaseModel):
    log_level: LogLevel = LogLevel.INFO


class NetworkConfig(BaseModel):
    protocol: NetworkProtocol = NetworkProtocol.TCP
    port_in: int = 5555
    port_out: int = 5556


class TTSConfig(BaseModel):
    model_name: str = "openbmb/VoxCPM2"
    reference_wav_path: str = "resources/source-ilja.wav"
    reference_text: str = "Das Scheinwerferlicht bricht sich in der Stille des großen Hauses, während der Vorhang langsam beiseite gleitet. In diesem flüchtigen Moment zwischen Realität und Illusion verschmelzen die Worte des Dramas mit der Präsenz des Schauspielers, um das Publikum in eine Welt voll dramatischer Tiefe und ungeahnter Leidenschaft zu entführen."


class GlobalConfig(BaseSettings):
    model_config = ConfigDict(frozen=True)
    system: SystemConfig = SystemConfig()
    network: NetworkConfig = NetworkConfig()
    tts: TTSConfig = TTSConfig()


settings = GlobalConfig()
