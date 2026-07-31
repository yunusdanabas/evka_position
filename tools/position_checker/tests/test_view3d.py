import sys

from PyQt5 import QtWidgets

from tools.position_checker.gui import _View3D
import pytest

# This module builds pyqtgraph plot widgets, which register in a process-global
# ViewBox registry that every later plot construction walks. Sharing one process
# across these modules segfaults intermittently, so run this one forked.
# See docs/CI_PYTEST_SEGFAULT_LOG.md.
pytestmark = pytest.mark.forked


def test_set_data_accepts_empty_lists_from_hidden_trail():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    view = _View3D()
    view.set_data([], [], [])
    view.set_data([1.0], [2.0], [3.0])
    assert view._pts == [(1.0, 2.0, 3.0)]
    view.close()
    assert app is not None
