# src/ssg_hs_forensics_app/config_loader.py

from __future__ import annotations

import sys
from pathlib import Path
import tomllib
from importlib.resources import files as pkg_files
from typing import Dict, Any, Tuple
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
    """
    Return the path to the built-in config.toml.
    FATAL if missing (OK to print here since application cannot run).
    """
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
    """Load the built-in TOML config shipped inside the package."""
    path = get_builtin_config_path()
    with path.open("rb") as f:
        return tomllib.load(f)


# ======================================================================
# User override config loader (silent)
# ======================================================================

def _load_user_override_folder(builtin_cfg: dict) -> Tuple[dict, str | None]:
    """
    Attempt to load user config.toml from application.config_folder.
    Returns:
        (user_cfg: dict, source_path: str|None)
    Never prints/logs — pure silent operation.
    """
    app_cfg = builtin_cfg.get("application", {})
    folder = app_cfg.get("config_folder")

    if not folder:
        return {}, None

    folder_path = Path(folder).expanduser().resolve()
    cfg_path = folder_path / CONFIG_FILENAME

    if not cfg_path.exists():
        return {}, None

    try:
        with cfg_path.open("rb") as f:
            return tomllib.load(f), str(cfg_path)
    except Exception:
        # Failed user config is silently ignored (CLI will report)
        return {}, None


# ======================================================================
# Public API
# ======================================================================

@lru_cache(maxsize=1)
def load_config(config_file_override: str | None = None) -> dict:
    """
    Load and merge:
        1. Built-in config (required)
        2. User override folder (optional)
        3. --config-file override (highest precedence)

    No prints/logging — caller logs events after Loguru initialization.
    """

    builtin = load_builtin_config()

    # --- Case 1: explicit CLI override file ---
    if config_file_override:
        override_path = Path(config_file_override)
        with override_path.open("rb") as f:
            override_cfg = tomllib.load(f)

        merged = _deep_merge(builtin, override_cfg)
        merged["_loaded_from"] = str(override_path)
        return merged

    # --- Case 2: built-in + user config folder (normal flow) ---
    user_cfg, user_path = _load_user_override_folder(builtin)
    merged = _deep_merge(builtin, user_cfg)
    merged["_loaded_from"] = user_path or "<built-in defaults>"

    return merged
