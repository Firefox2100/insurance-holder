import os
import logging
import secrets
import importlib.resources
from typing import Optional, Literal
from argon2 import PasswordHasher
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


SECRETS_DIR = '/run/secrets' if os.path.isdir('/run/secrets') else None
STATIC_FILE_PATH = importlib.resources.files('insurance_holder.data') / 'static'


class Settings(BaseSettings):
    """
    Configurations for the Biomedical Terminology Service.
    """

    model_config = SettingsConfigDict(
        env_prefix='IH_',
        env_file_encoding='utf-8',
        **({'secrets_dir': SECRETS_DIR} if SECRETS_DIR else {})
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
        description='Whether this application is behind an HTTPS proxy. This affects cookie '
                    'settings, redirect URLs, and security headers.',
    )

    database_url: str = Field(
        ...,
        description='Database connection string for the application',
    )


CONFIG = Settings(_env_file=os.getenv('IH_ENV_FILE', '.env'))   # type: ignore
LOGGER = logging.getLogger('Insurance Holder')
LOGGER.setLevel(CONFIG.logging_level.upper())

if not LOGGER.hasHandlers():
    console_handler = logging.StreamHandler()
    console_handler.setLevel(CONFIG.logging_level.upper())

    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(process)d] [%(levelname)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %z'
    )
    console_handler.setFormatter(formatter)

    LOGGER.addHandler(console_handler)


PH = PasswordHasher()
