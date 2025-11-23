"""
Unified configuration loader.

Responsibilities:
- Load built-in config from package (required)
- Optionally load user config override from application.config_folder
- Deep-merge the two configs
- Expose a single load_config() method
"""

from __future__ import annotations

import sys
from pathlib import Path
import tomllib
from importlib.resources import files as pkg_files
from typing import Dict, Any
from functools import lru_cache

CONFIG_FILENAME = "config.toml"


# ======================================================================
# Helpers
# ======================================================================

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two dictionaries, with `override` taking precedence."""

    result = base.copy()
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


# ======================================================================
# Built-in config loader
# ======================================================================

def get_builtin_config_path() -> Path:
    """Return the path to the built-in config.toml bundled inside the package."""
    try:
        pkg_root = pkg_files("ssg_hs_forensics_app") / "config"
        cfg_file = pkg_root / CONFIG_FILENAME

        cfg_path = Path(cfg_file)
        if cfg_path.is_file():
            return cfg_path

    except Exception:
        pass

    print(
        f"\nFATAL ERROR: Missing built-in configuration file "
        f"`ssg_hs_forensics_app/config/{CONFIG_FILENAME}`.\n",
        file=sys.stderr,
    )
    sys.exit(1)


def load_builtin_config() -> dict:
    """Load the built-in TOML config shipped with the package."""
    path = get_builtin_config_path()
    with path.open("rb") as f:
        data = tomllib.load(f)

    # ❌ REMOVE this line:
    # data["__config_file__"] = str(path)

    return data


# ======================================================================
# User override config loader
# ======================================================================

def _load_user_override_folder(builtin_cfg: dict) -> dict:
    """
    Attempt to load user config.toml from application.config_folder.
    Return empty dict if not found.
    """

    app_cfg = builtin_cfg.get("application", {})
    folder = app_cfg.get("config_folder")

    if not folder:
        return {}

    folder_path = Path(folder).expanduser().resolve()
    cfg_path = folder_path / CONFIG_FILENAME

    if not cfg_path.exists():
        print(
            f"[config] No user config override found at: {cfg_path}",
            file=sys.stderr,
        )
        return {}

    try:
        with cfg_path.open("rb") as f:
            print(f"[config] Loaded user override: {cfg_path}")
            return tomllib.load(f)
    except Exception as e:
        print(f"[config] WARNING: Failed to load user config: {e}", file=sys.stderr)
        return {}


# ======================================================================
# Public API
# ======================================================================

@lru_cache(maxsize=1)
def load_config() -> dict:
    """
    Load and merge:
        1. built-in config (required)
        2. user config override (optional)
    """

    builtin = load_builtin_config()
    user = _load_user_override_folder(builtin)

    # Deep merge user → builtin
    merged = _deep_merge(builtin, user)

    return merged
