# src/ssg_hs_forensics_app/core/config.py

"""
Singleton accessor for merged configuration.
"""

from __future__ import annotations

from ssg_hs_forensics_app.config_loader import load_config


def get_config() -> dict:
    """
    Return merged config (built-in + user override), cached for all callers.
    """
    return load_config()
