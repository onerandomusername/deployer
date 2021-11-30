import logging
import os
import pathlib
from dataclasses import dataclass
from typing import Optional

import dotenv

from deployer.dirs import dirs


env = os.environ.copy()
env.update(dotenv.dotenv_values(dotenv.find_dotenv(env.get("ENV_FILE", ".env"))))


@dataclass
class Config:
    """Config dataclass Holds necessary config for operation."""

    repo: str = env["REPO"]
    data_dir: pathlib.Path = pathlib.Path(env.get("CLONE_DIR", dirs.user_cache_path))
    command: str = env["ENTRY_COMMAND"]


@dataclass
class LoggingConfig:
    """Send alerts and stuff to a discord webhook."""

    enabled: bool = False
    webhook_id: Optional[int] = int(env.get("WEBHOOK_ID", 0)) or None
    webhook_token: Optional[str] = env.get("WEBHOOK_TOKEN")
    relay_level: int = int(env.get("LOGGING_RELAY_LEVEL", logging.WARNING))


LoggingConfig.enabled = LoggingConfig.webhook_id is not None and LoggingConfig.webhook_token is not None


@dataclass
class GithubAPI:
    """Github api configuration."""

    token: Optional[str] = env.get("GITHUB_TOKEN")
    root: str = env.get("GITHUB_HOST", "https://api.github.com")
