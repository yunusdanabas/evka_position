"""test_ipt_panel.py — inline IptPanel behavior."""

import sys

import numpy as np
import pytest
from PyQt5 import QtWidgets

from tools.evka_gui.ipt_panel import IptPanel


@pytest.fixture(scope="module")
def qapp():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    return app


def test_buttons_disabled_until_connected(qapp):
    panel = IptPanel()
    assert not panel.btn_arm.isEnabled()
    panel.set_connected(True)
    assert panel.btn_arm.isEnabled()
    panel.set_connected(False)
    assert not panel.btn_arm.isEnabled()


def test_arm_and_feed_increments_count(qapp):
    panel = IptPanel()
    panel.set_connected(True)
    panel._arm()
    panel.feed_line("X10.00,Y20.00,Z30.00")
    panel.feed_line("SENSOR,100.00,0.000,0.000,1,1")
    assert panel.count() == 1
    np.testing.assert_allclose(panel.points()[0], [10, 20, 30])


def test_show_overlay_when_armed_or_has_points(qapp):
    panel = IptPanel()
    assert not panel.show_overlay()
    panel.set_connected(True)
    panel._arm()
    assert panel.show_overlay()
    panel._stop()
    panel._clear()
    assert not panel.show_overlay()
