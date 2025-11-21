from click.testing import CliRunner
from pathlib import Path
import tempfile

from ssg_hs_forensics_app.cli._main import cli

def test_config_show_when_missing(monkeypatch):
    """
    `sammy config show` should not crash when the config file does not exist.
    """

    # Point DEFAULT_CONFIG_PATH to a non-existent temporary location
    tmpdir = tempfile.mkdtemp()
    missing_path = Path(tmpdir) / "config.yaml"

    monkeypatch.setattr(
        "ssg_hs_forensics_app.config_loader.DEFAULT_CONFIG_PATH",
        missing_path,
        raising=True
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["config", "show"])

    assert result.exit_code == 0, f"CLI crashed:\n{result.output}"
    assert "Config file not found" in result.output
