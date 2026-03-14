# -*- coding: utf-8 -*-

from enum import Enum

from pydantic import (
    Field,
    SecretStr,
)
from pydantic_settings import SettingsConfigDict

from api.core.constants import ENV_PREFIX
from ._base import FrozenBaseConfig, BaseConfig


class ChallengeStatusEnum(str, Enum):
    ACTIVE = "active"
    RUNNING = "running"
    COMPLETED = "completed"


class ChallengeConfig(BaseConfig):
    api_key: SecretStr = Field(..., min_length=8, max_length=128)
    single_request_timeout: int = Field(default=2, ge=1)
    acceptable_miss_count: int = Field(default=10, ge=0)
    fingerprinter_ip: str = Field(
        "0.0.0.0", strip_whitespace=True, min_length=7, max_length=15
    )
    fingerprinter_port: int = Field(default=8000, ge=1, le=65535)
    metrics_csv_path: str = Field(
        ..., strip_whitespace=True, min_length=2, max_length=256
    )
    submission_fns: list[str] = Field(
        default=["initializer", "metrics_collector", "linker"], min_items=1
    )
    submission_length_limit: int = Field(default=1000, ge=1)
    model_config = SettingsConfigDict(env_prefix=f"{ENV_PREFIX}CHALLENGE_")


__all__ = [
    "ChallengeConfig",
    "ChallengeStatusEnum",
]
