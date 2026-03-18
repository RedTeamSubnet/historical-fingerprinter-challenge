import os
from enum import Enum
from typing_extensions import Self

from pydantic import (
    BaseModel,
    Field,
    SecretStr,
    model_validator,
)
from pydantic_settings import SettingsConfigDict

from api.core.constants import ENV_PREFIX
from ._base import BaseConfig

_API_DIR_ENV = "HFP_CHALLENGE_API_DIR"
_DEFAULT_API_DIR = "/app/rest-hfp-challenge"


class ChallengeStatusEnum(str, Enum):
    ACTIVE = "active"
    RUNNING = "running"
    COMPLETED = "completed"


class FrameworkImageConfig(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    image: str = Field(..., min_length=1, max_length=256)


class FingerpinterContainerConfig(BaseModel):
    network_name: str = Field(default="internal_net")
    image: str = Field(default="redteamsubnet61/hfp_fingerprinter:latest")
    build_path: str = Field(
        default="{api_dir}/fingerprinter",
        description=(
            "Path to the fingerprinter build context. "
            "Use {api_dir} as a placeholder to expand against HFP_CHALLENGE_API_DIR."
        ),
    )

    @model_validator(mode="after")
    def _expand_paths(self) -> Self:
        api_dir = os.getenv("HFP_CHALLENGE_API_DIR", _DEFAULT_API_DIR)
        if "{api_dir}" in self.build_path:
            self.build_path = self.build_path.format(api_dir=api_dir)
        return self


class ScoringConfig(BaseModel):
    testcase_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "webgl": 1.0,
            "webgpuliar": 1.0,
            "audio": 1.0,
            "fonts": 0.8,
        }
    )
    browser_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "chrome": 1.0,
            "firefox": 1.0,
            "brave": 0.9,
            "safari": 0.9,
        }
    )
    collision_penalty: float = Field(default=0.3, ge=0.0, le=1.0)
    fragmentation_penalty: float = Field(default=0.2, ge=0.0, le=1.0)
    max_collision_threshold: int = Field(default=2, ge=1)
    max_fragmentation_threshold: int = Field(default=3, ge=1)


class ChallengeConfig(BaseConfig):
    api_key: SecretStr = Field(..., min_length=8, max_length=128)
    single_request_timeout: int = Field(default=2, ge=1)
    acceptable_miss_count: int = Field(default=10, ge=0)
    fingerprinter_ip: str = Field(
        "127.0.0.1", strip_whitespace=True, min_length=7, max_length=15
    )
    fingerprinter_port: int = Field(default=8000, ge=1, le=65535)
    metrics_csv_path: str = Field(
        ..., strip_whitespace=True, min_length=2, max_length=256
    )
    submission_fns: list[str] = Field(
        default=["initializer", "metrics_collector", "linker"], min_items=1
    )
    submission_length_limit: int = Field(default=1000, ge=1)
    framework_images: list[FrameworkImageConfig] = Field(default_factory=list)
    repeated_framework_count: int = Field(default=3, ge=1)
    human_injection_count: int = Field(default=1, ge=0)
    allowed_webdriver_miss_count: int = Field(default=2, ge=0)
    allowed_websocket_miss_count: int = Field(default=2, ge=0)
    allowed_human_miss_count: int = Field(default=1, ge=0)
    fp_container: FingerpinterContainerConfig = Field(
        default_factory=FingerpinterContainerConfig
    )
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    model_config = SettingsConfigDict(env_prefix=f"{ENV_PREFIX}CHALLENGE_")


__all__ = [
    "ChallengeConfig",
    "ChallengeStatusEnum",
    "FrameworkImageConfig",
    "FingerpinterContainerConfig",
    "ScoringConfig",
]
