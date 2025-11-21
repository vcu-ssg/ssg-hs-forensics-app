import yaml
from click.testing import CliRunner
from pathlib import Path
import tempfile

import ssg_hs_forensics_app.config_loader as cl
from ssg_hs_forensics_app.cli._main import cli


def test_config_show_when_missing(monkeypatch):
    tempdir = tempfile.mkdtemp()
    missing_file = Path(tempdir) / "missing.yaml"

    monkeypatch.setattr(
        "ssg_hs_forensics_app.cli.config_cmd.DEFAULT_CONFIG_PATH",
        missing_file,
        raising=True
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "show"])

    assert result.exit_code == 0
    assert "Config file not found" in result.output


def test_config_show_when_present(monkeypatch):
    tempdir = tempfile.mkdtemp()
    cfg_file = Path(tempdir) / "config.yaml"
    cfg_file.write_text("sam: {x: 1}")

    monkeypatch.setattr(
        "ssg_hs_forensics_app.cli.config_cmd.DEFAULT_CONFIG_PATH",
        cfg_file,
        raising=True
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "show"])

    assert result.exit_code == 0
    data = yaml.safe_load(result.output)
    assert data == {"sam": {"x": 1}}

