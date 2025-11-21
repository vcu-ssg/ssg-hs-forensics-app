from click.testing import CliRunner
from pathlib import Path
import tempfile

import ssg_hs_forensics_app.config_loader as cl
from ssg_hs_forensics_app.cli._main import cli


def test_config_init_force_overwrite(monkeypatch):
    tmp = Path(tempfile.mkdtemp())

    # Fake repo config
    cfg_dir = tmp / "config"
    cfg_dir.mkdir()
    src1 = cfg_dir / "sam_defaults.yaml"
    src1.write_text("sam: {original: 1}")

    # User config dir (existing file)
    user_cfg = tmp / "user"
    user_cfg.mkdir()
    dst1 = user_cfg / "sam_defaults.yaml"
    dst1.write_text("sam: {old: 999}")

    # Force loader to repo mode
    src_dir = tmp / "src/ssg_hs_forensics_app"
    src_dir.mkdir(parents=True)
    fake_loader = src_dir / "config_loader.py"
    fake_loader.touch()
    monkeypatch.setattr(cl, "__file__", str(fake_loader))

    # IMPORTANT FIX: patch the correct module with the correct path
    monkeypatch.setattr(
        "ssg_hs_forensics_app.cli.config_cmd.DEFAULT_CONFIG_PATH",
        user_cfg / "dummy.yaml",
        raising=True
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["config", "init", "--force"])

    assert result.exit_code == 0

    # Confirm overwritten file contents
    assert dst1.read_text() == "sam: {original: 1}"
