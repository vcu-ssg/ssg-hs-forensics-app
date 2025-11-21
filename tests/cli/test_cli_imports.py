def test_cli_imports_default_config_path():
    """
    Ensures the CLI can import DEFAULT_CONFIG_PATH.
    This catches ImportError issues not covered by current tests.
    """
    try:
        from ssg_hs_forensics_app.cli.config_cmd import DEFAULT_CONFIG_PATH
    except ImportError as e:
        raise AssertionError(f"CLI failed to import DEFAULT_CONFIG_PATH: {e}")
