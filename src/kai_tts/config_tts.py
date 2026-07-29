from typing import Tuple, Type
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)
from kai_shared.config_shared import SharedConfig
# from pydantic import BaseModel


class TTSConfig(BaseSettings):
    model_config = SettingsConfigDict(toml_file="config.toml")
    shared: SharedConfig = SharedConfig()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls),)


settings_tts = TTSConfig()
