import dataclasses
import json
import os
import os.path
import pathlib


def default_config_dir() -> pathlib.Path:
    if os.getenv("XDG_CONFIG_HOME"):
        config_root = pathlib.Path(os.getenv("XDG_CONFIG_HOME"))
    else:
        config_root = pathlib.Path.home() / ".config"
    return config_root / "scimma-aws"


def default_config_file() -> pathlib.Path:
    return default_config_dir() / "config"


def default_cache_dir() -> pathlib.Path:
    return default_config_dir() / "cache"


@dataclasses.dataclass
class Config:
    username: str
    password: str
    entity_id: str
    region: str
    profile_name: str
    role_arn: str = ""

    def to_file(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        config_data = {
            "username": self.username,
            "password": self.password,
            "entity_id": self.entity_id,
            "region": self.region,
            "profile_name": self.profile_name,
            "role_arn": self.role_arn,
        }
        with open(filepath, "w") as f:
            json.dump(config_data, f)
        os.chmod(filepath, 0o600)

    @classmethod
    def from_file(cls, filepath):
        data = json.load(open(filepath, "r"))
        return Config(**data)
