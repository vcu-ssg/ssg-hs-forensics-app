from click.testing import CliRunner
from pathlib import Path
import tempfile
import yaml

import ssg_hs_forensics_app.config_loader as cl
from ssg_hs_forensics_app.cli._main import cli


def test_config_init_installed_mode(monkeypatch, tmp_path):
    # Force repo mode off
    monkeypatch.setattr(cl, "get_repo_config_dir", lambda: None)

    # Simulate packaged default files (not modules)
    pkg_cfg = tmp_path / "pkg"
    pkg_cfg.mkdir()
    sam_file = pkg_cfg / "sam_defaults.yaml"
    other_file = pkg_cfg / "other.yaml"
    sam_file.write_text("sam: {c: 3}")
    other_file.write_text("other: {d: 4}")

    # Monkeypatch active default files directly
    monkeypatch.setattr(
        cl,
        "get_active_default_config_files",
        lambda: [sam_file, other_file],
    )

    # Fake user config location
    user_cfg_root = tmp_path / "user"
    user_cfg_root.mkdir()
    monkeypatch.setattr(
        "ssg_hs_forensics_app.cli.config_cmd.DEFAULT_CONFIG_PATH",
        user_cfg_root / "config.yaml",
        raising=True
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["config", "init"])

    assert result.exit_code == 0
    assert (user_cfg_root / "sam_defaults.yaml").exists()
    assert (user_cfg_root / "other.yaml").exists()

    # Verify content
    assert yaml.safe_load((user_cfg_root / "sam_defaults.yaml").read_text()) == {"sam": {"c": 3}}
    assert yaml.safe_load((user_cfg_root / "other.yaml").read_text()) == {"other": {"d": 4}}
