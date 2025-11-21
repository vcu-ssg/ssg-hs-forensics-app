from click.testing import CliRunner
from pathlib import Path
import tempfile

import ssg_hs_forensics_app.config_loader as cl
from ssg_hs_forensics_app.cli._main import cli


def test_config_init_repo_mode(monkeypatch):
    repo = Path(tempfile.mkdtemp())
    src_dir = repo / "src" / "ssg_hs_forensics_app"
    src_dir.mkdir(parents=True)

    # Fake repo defaults
    cfg_dir = repo / "config"
    cfg_dir.mkdir()
    (cfg_dir / "sam_defaults.yaml").write_text("sam: {a: 1}")
    (cfg_dir / "extra.yaml").write_text("extra: {b: 2}")

    # Fake loader location
    fake_loader = src_dir / "config_loader.py"
    fake_loader.touch()
    monkeypatch.setattr(cl, "__file__", str(fake_loader))

    # User config should go here
    user_cfg_root = Path(tempfile.mkdtemp())
    monkeypatch.setattr(
        "ssg_hs_forensics_app.cli.config_cmd.DEFAULT_CONFIG_PATH",
        user_cfg_root / "config.yaml",
        raising=True
    )    

    runner = CliRunner()
    result = runner.invoke(cli, ["config", "init"])

    assert result.exit_code == 0

    # Confirm both files copied
    assert (user_cfg_root / "sam_defaults.yaml").exists()
    assert (user_cfg_root / "extra.yaml").exists()
