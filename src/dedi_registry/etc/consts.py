import os
import logging
import secrets
from typing import Literal
from argon2 import PasswordHasher
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from dedi_registry.etc.enums import DatabaseDriverType, CacheDriverType


class Settings(BaseSettings):
    """
    Configurations for the Decentralised Discovery Network Registry backend.
    """
    model_config = SettingsConfigDict(
        env_prefix='DR_',
        env_file_encoding='utf-8',
    )

    auto_approve: bool = Field(
        False,
        description='Automatically approve network registration requests for unattended deployments',
    )
    allow_origins: list[str] = Field(
        default_factory=list,
        description='List of allowed origins for CORS requests',
    )
    trusted_proxies: list[str] = Field(
        default_factory=list,
        description='List of trusted proxy IP addresses for correct client IP resolution',
    )

    database_driver: DatabaseDriverType = Field(
        DatabaseDriverType.MONGO,
        description='Database driver to use for the service',
    )
    mongodb_host: str = Field(
        'localhost',
        description='Host for the MongoDB database',
    )
    mongodb_port: int = Field(
        27017,
        description='Port for the MongoDB database',
    )
    mongodb_db_name: str = Field(
        'ddn-registry',
        description='Name of the MongoDB database to use',
    )

    cache_driver: CacheDriverType = Field(
        CacheDriverType.REDIS,
        description='Cache driver to use for the service',
    )
    redis_host: str = Field(
        'localhost',
        description='Redis host for the cache',
    )
    redis_port: int = Field(
        6379,
        description='Redis port for the cache',
    )

    logging_level: Literal['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'] = Field(
        'INFO',
        description='Logging level for the application'
    )
    secret_key: str = Field(
        default_factory=secrets.token_urlsafe,
        description='Secret key for the application',
    )
    use_https: bool = Field(
        False,
        description='Whether this application is behind an HTTPS proxy. This affects cookie settings, '
                    'redirect URLs, and security headers.',
    )


CONFIG = Settings(_env_file=os.getenv('DR_ENV_FILE', 'conf/.env'))      # type: ignore
LOGGER = logging.getLogger('Decentralised Discovery Network Registry')
LOGGER.setLevel(CONFIG.logging_level.upper())   # pylint: disable=no-member

if not LOGGER.hasHandlers():
    console_handler = logging.StreamHandler()
    console_handler.setLevel(CONFIG.logging_level.upper())      # pylint: disable=no-member

    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(process)d] [%(levelname)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %z'
    )
    console_handler.setFormatter(formatter)

    LOGGER.addHandler(console_handler)


LOGGER.debug('System configuration loaded: %s', CONFIG.model_dump_json())

PH = PasswordHasher()
