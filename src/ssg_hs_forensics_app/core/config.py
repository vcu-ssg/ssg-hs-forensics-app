# src/ssg_hs_forensics_app/core/config.py

"""
Singleton accessor for merged configuration.
"""

from __future__ import annotations
from functools import lru_cache

from ssg_hs_forensics_app.config_loader import load_config


@lru_cache(maxsize=1)
def get_config() -> dict:
    """
    Return merged config (built-in + user override), cached for all callers.
    """
    return load_config()
