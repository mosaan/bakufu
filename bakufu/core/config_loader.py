"""Configuration loader for bakufu.yml files"""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from .exceptions import ConfigurationError


class ProviderConfig(BaseModel):
    """Configuration for a specific AI provider"""

    api_key: str | None = None
    organization: str | None = None
    region: str | None = None
    base_url: str | None = None
    timeout: int | None = None

    @field_validator("api_key", "organization", "region", "base_url")
    @classmethod
    def expand_env_vars(cls, v: str | None) -> str | None:
        """Expand environment variables in configuration values"""
        if v is None:
            return v

        # Handle ${VAR} format
        if v.startswith("${") and v.endswith("}"):
            env_var = v[2:-1]
            return os.getenv(env_var)

        # Handle $VAR format
        if v.startswith("$"):
            env_var = v[1:]
            return os.getenv(env_var)

        return v


class BakufuConfig(BaseModel):
    """Main bakufu configuration"""

    default_provider: str = "gemini/gemini-2.0-flash"
    timeout_per_step: int = Field(default=60, gt=0)
    max_parallel_ai_calls: int = Field(default=3, gt=0)
    max_parallel_text_processing: int = Field(default=5, gt=0)
    max_auto_retry_attempts: int = Field(
        default=10, ge=0, description="Maximum auto-retry attempts when AI response is truncated"
    )

    provider_settings: dict[str, ProviderConfig] = Field(default_factory=dict)

    # Additional configuration options
    log_level: str = "INFO"
    cache_enabled: bool = True

    # MCP Large Output Control Settings
    mcp_max_output_chars: int = Field(default=8000, gt=0)
    mcp_auto_file_output_dir: str = Field(default="./mcp_outputs")

    @field_validator("provider_settings", mode="before")
    @classmethod
    def convert_provider_settings(cls, v: dict[str, Any]) -> dict[str, ProviderConfig]:
        """Convert raw dict to ProviderConfig objects"""
        if not isinstance(v, dict):
            return {}

        result = {}
        for provider_name, settings in v.items():
            if isinstance(settings, dict):
                result[provider_name] = ProviderConfig(**settings)
            else:
                result[provider_name] = settings

        return result


class ConfigLoader:
    """Configuration file loader with hierarchy support"""

    @staticmethod
    def find_config_files() -> list[Path]:
        """Find configuration files in order of precedence"""
        config_files = []

        # 1. Current directory bakufu.yml
        current_dir = Path.cwd()
        project_config = current_dir / "bakufu.yml"
        if project_config.exists():
            config_files.append(project_config)

        # 2. User config directory
        user_config_dir = Path.home() / ".config" / "bakufu"
        user_config = user_config_dir / "config.yml"
        if user_config.exists():
            config_files.append(user_config)

        # 3. Environment variable specified config
        env_config_path = os.getenv("BAKUFU_CONFIG")
        if env_config_path:
            env_config = Path(env_config_path)
            if env_config.exists():
                config_files.append(env_config)

        return config_files

    @staticmethod
    def load_config_from_file(config_path: Path) -> dict[str, Any]:
        """Load configuration from a single YAML file"""
        try:
            with open(config_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            if config_data is None:
                return {}

            if not isinstance(config_data, dict):
                raise ConfigurationError(
                    f"Configuration file {config_path} must contain a YAML dictionary"
                )

            return config_data

        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML in configuration file {config_path}: {e}"
            ) from e
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from {config_path}: {e}") from e

    @staticmethod
    def merge_configs(configs: list[dict[str, Any]]) -> dict[str, Any]:
        """Merge multiple configuration dictionaries"""
        merged: dict[str, Any] = {}

        for config in configs:
            for key, value in config.items():
                if key == "provider_settings" and isinstance(value, dict):
                    # Special handling for provider_settings - merge nested dicts
                    if "provider_settings" not in merged:
                        merged["provider_settings"] = {}
                    merged["provider_settings"].update(value)
                else:
                    # For other keys, later configs override earlier ones
                    merged[key] = value

        return merged

    @classmethod
    def load_config(cls, config_path: Path | None = None) -> BakufuConfig:
        """Load configuration from files and environment variables"""
        if config_path:
            # Load from specific file
            if not config_path.exists():
                raise ConfigurationError(f"Configuration file not found: {config_path}")

            config_data = cls.load_config_from_file(config_path)
            return BakufuConfig(**config_data)

        # Load from multiple sources
        config_files = cls.find_config_files()

        if not config_files:
            # No config files found, return default configuration
            return BakufuConfig()

        # Load and merge all config files
        configs = []
        for config_file in reversed(config_files):  # Reverse order for proper precedence
            try:
                config_data = cls.load_config_from_file(config_file)
                configs.append(config_data)
            except ConfigurationError:
                # Skip files that can't be loaded
                continue

        if not configs:
            return BakufuConfig()

        merged_config = cls.merge_configs(configs)

        try:
            return BakufuConfig(**merged_config)
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration: {e}") from e

    @staticmethod
    def create_default_config(config_path: Path) -> None:
        """Create a default configuration file"""
        default_config = {
            "default_provider": "gemini/gemini-2.0-flash",
            "timeout_per_step": 60,
            "max_parallel_ai_calls": 3,
            "max_parallel_text_processing": 5,
            "log_level": "INFO",
            "cache_enabled": True,
            "provider_settings": {
                "gemini": {"api_key": "${GOOGLE_API_KEY}", "region": "asia-northeast1"},
                "openai": {"api_key": "${OPENAI_API_KEY}", "organization": "your-org-id"},
                "anthropic": {"api_key": "${ANTHROPIC_API_KEY}"},
            },
        }

        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(
                default_config, f, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
