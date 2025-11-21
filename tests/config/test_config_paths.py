from pathlib import Path
import tempfile
import shutil

import ssg_hs_forensics_app.config_loader as cl


def test_get_default_config_path_exists():
    p = cl.DEFAULT_CONFIG_PATH
    assert isinstance(p, Path)


def test_repo_config_dir_detected_when_present(monkeypatch):
    tmp = Path(tempfile.mkdtemp())
    repo_root = tmp
    src_dir = repo_root / "src" / "ssg_hs_forensics_app"
    src_dir.mkdir(parents=True)
    cfg_dir = repo_root / "config"
    cfg_dir.mkdir()
    (cfg_dir / "sam_defaults.yaml").write_text("sam: {x: 1}")

    # Patch __file__ location to simulate running from repo
    fake_loader = src_dir / "config_loader.py"
    fake_loader.touch()

    monkeypatch.setattr(cl, "__file__", str(fake_loader))

    repo_cfg = cl.get_repo_config_dir()
    assert repo_cfg == cfg_dir


def test_repo_config_dir_none_when_missing(monkeypatch):
    tmp = Path(tempfile.mkdtemp())
    repo_root = tmp
    src_dir = repo_root / "src" / "ssg_hs_forensics_app"
    src_dir.mkdir(parents=True)

    fake_loader = src_dir / "config_loader.py"
    fake_loader.touch()

    monkeypatch.setattr(cl, "__file__", str(fake_loader))

    assert cl.get_repo_config_dir() is None


def test_active_default_files_repo_mode(monkeypatch):
    tmp = Path(tempfile.mkdtemp())
    repo_root = tmp
    src_dir = repo_root / "src" / "ssg_hs_forensics_app"
    src_dir.mkdir(parents=True)

    cfg_dir = repo_root / "config"
    cfg_dir.mkdir()
    (cfg_dir / "one.yaml").write_text("a: 1")
    (cfg_dir / "two.yml").write_text("b: 2")

    fake_loader = src_dir / "config_loader.py"
    fake_loader.touch()

    monkeypatch.setattr(cl, "__file__", str(fake_loader))

    files = cl.get_active_default_config_files()
    assert sorted(p.name for p in files) == ["one.yaml", "two.yml"]
