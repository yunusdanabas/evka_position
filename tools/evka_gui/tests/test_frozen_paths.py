"""Paths that must survive being frozen into a PyInstaller bundle.

These two branches only misbehave in a packaged build, where nobody runs a test
suite — so they get checked here instead.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest
from PyQt5 import QtWidgets

import tools.calibration.report as report


@pytest.fixture(scope="module")
def qapp():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)


@pytest.fixture
def frozen(monkeypatch):
    """Make the interpreter look like a PyInstaller bundle, then restore."""
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    yield
    importlib.reload(report)  # leave the module in its real, non-frozen state


def test_project_root_is_repo_root_from_source():
    assert (report.PROJECT_ROOT / "pyproject.toml").exists()


def test_project_root_moves_to_localappdata_when_frozen(frozen, monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    importlib.reload(report)

    assert report.PROJECT_ROOT == tmp_path / "evka_position"
    # The session dir must stay under the new root, not the bundle.
    assert report.DEFAULT_SESSION_DIR.is_relative_to(report.PROJECT_ROOT)


def test_project_root_uses_xdg_data_home_when_set(frozen, monkeypatch, tmp_path):
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    importlib.reload(report)

    assert report.PROJECT_ROOT == tmp_path / "evka_position"


def test_project_root_never_lands_on_the_repo_itself(frozen, monkeypatch, tmp_path):
    """The bare-home fallback used to collide with a repo checked out under ~."""
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    importlib.reload(report)

    assert report.PROJECT_ROOT == tmp_path / ".local" / "share" / "evka_position"
    assert report.PROJECT_ROOT != tmp_path / "evka_position"


def test_deploy_json_follows_project_root(frozen, monkeypatch, tmp_path):
    """calibration.py writes DEPLOY_JSON; it must not land inside the bundle."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    importlib.reload(report)

    deploy_json = report.PROJECT_ROOT / "tools" / "calibration" / "calibration.json"
    assert deploy_json.is_relative_to(tmp_path)


def test_default_export_path_is_absolute(qapp):
    from tools.evka_gui.session_utils import default_export_path

    path = default_export_path("evka_points_123.csv")

    # A bare filename would resolve against cwd — the app folder in a frozen
    # build, where the user can't find it and may not be able to write it.
    assert os.path.isabs(path)
    assert path.endswith("evka_points_123.csv")
