#!/usr/bin/env python3

import logging
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

base_config = ConfigDict(validate_default=True, extra="forbid")


class ProjectsConfig(BaseModel):
    model_config = base_config

    organization: str
    projects: list[str]
    external_projects: list[str]
    version_re: str


class Config(BaseModel):
    model_config = base_config

    projects: ProjectsConfig
    unstable_debian_branches: dict[str, str]


def get_config(path: Path | None = None) -> Config:
    project_dir = Path(__file__).parent.parent.parent

    settings_path = path or (project_dir / "config" / "config.toml")
    toml = tomllib.load(settings_path.open("rb"))

    try:
        config = Config(**toml)
    except ValidationError as err:
        errmsg = f"Errors found in the configuration file {settings_path}!\n\n"
        for error in err.errors():
            full_loc = ".".join(str(loc) for loc in error["loc"])
            errmsg += f"  {full_loc}: {error['msg']}\n"
        logging.error(errmsg)
        raise SystemExit(1) from None

    return config
