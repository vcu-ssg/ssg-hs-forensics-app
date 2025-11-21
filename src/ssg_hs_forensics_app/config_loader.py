"""
Load the *built-in* application configuration from:
    ssg_hs_forensics_app/config/config.toml

There is no user config and no repo-mode config.
The program will terminate if the built-in config is missing.
"""

from __future__ import annotations

import sys
from pathlib import Path
import tomllib
from importlib.resources import files as pkg_files


CONFIG_FILENAME = "config.toml"


# ============================================================
# INTERNAL — Locate config.toml inside the installed module
# ============================================================

def get_builtin_config_path() -> Path:
    """
    Always load config from the module's own package data:
        ssg_hs_forensics_app/config/config.toml

    If the file does not exist, exit the program.
    """
    try:
        pkg_root = pkg_files("ssg_hs_forensics_app") / "config"
        cfg_file = pkg_root / CONFIG_FILENAME

        if cfg_file.is_file():
            return Path(cfg_file)

    except Exception:
        pass

    print(
        f"\nFATAL ERROR: Missing built-in configuration file "
        f"`ssg_hs_forensics_app/config/{CONFIG_FILENAME}`.\n",
        file=sys.stderr,
    )
    sys.exit(1)


# ============================================================
# LOADING
# ============================================================

def load_builtin_config() -> dict:
    """Load the module-shipped TOML config. Always succeed or exit."""
    cfg_path = get_builtin_config_path()

    try:
        with cfg_path.open("rb") as f:
            return tomllib.load(f)
    except Exception as e:
        print(
            f"\nFATAL ERROR: Could not parse TOML config at {cfg_path}:\n{e}\n",
            file=sys.stderr,
        )
        sys.exit(1)

# ============================================================
# Helpers (keep these for SAM logic + tests)
# ============================================================

def get_resolved_checkpoint_path(cfg: dict) -> Path | None:
    """
    Returns the checkpoint path as an absolute path.
    Used by SAM loader tests.
    """
    try:
        p = Path(cfg["sam"]["checkpoint"])
    except Exception:
        return None

    return p.resolve()
