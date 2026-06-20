"""Environment resolution for multi-environment configuration support.

Priority: CHATCHAT_ENV env var > "dev" default
Valid values: dev, staging, prod

Supports environment-specific config file overlay:
    basic_settings.yaml -> basic_settings.prod.yaml (if CHATCHAT_ENV=prod)
"""
import os
from pathlib import Path
from typing import Literal

Environment = Literal["dev", "staging", "prod"]

VALID_ENVIRONMENTS = ("dev", "staging", "prod")


def get_environment() -> Environment:
    env = os.environ.get("CHATCHAT_ENV", "dev").lower()
    if env not in VALID_ENVIRONMENTS:
        msg = f"Invalid CHATCHAT_ENV '{env}', must be one of {VALID_ENVIRONMENTS}"
        raise ValueError(msg)
    return env


def resolve_config_path(base_root: Path, filename: str | Path) -> Path:
    """Resolve config file path with environment overlay.

    If an env-specific file exists (e.g. basic_settings.prod.yaml),
    use it; otherwise fall back to the base file.

    Example:
        resolve_config_path(CHATCHAT_ROOT, "basic_settings.yaml")
        # With CHATCHAT_ENV=prod, returns basic_settings.prod.yaml if it exists
    """
    env = get_environment()
    path = Path(filename)
    stem = path.stem
    suffix = path.suffix
    env_file = base_root / f"{stem}.{env}{suffix}"
    if env_file.exists():
        return env_file
    return base_root / filename
