#!/usr/bin/env python3
"""remote_test_gui.py — Minimal PyQt5 GUI for testing the ESP32-C3 button remote.

Connects to the ButtonRemoteTest firmware over TCP (WiFi AP "REMOTE_TEST").
Shows live button press events for all 5 buttons and heartbeat status.

Usage:
    python tools/remote_tester/remote_test_gui.py

Firmware AP:  REMOTE_TEST / remote1234
Default IP:   192.168.4.1
Default port: 8080
"""

from __future__ import annotations

import datetime
import queue
import socket
import sys
import threading

from PyQt5 import QtCore, QtGui, QtWidgets

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_IP   = "192.168.4.1"
DEFAULT_PORT = "8080"
BTN_COUNT    = 5

_BTN_LABELS = ["BTN0\n(ADD\nPOINT)", "BTN1\n(DEL\nPOINT)", "BTN2\n(GPIO0)", "BTN3\n(GPIO1)", "BTN4\n(GPIO3)"]

_LED_SIZE = " border-radius: 14px; min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px;"

# Per-button idle styles: BTN0=green border, BTN1=red border, others=grey
_LED_IDLE_STYLES = [
    "background: #1e1e1e; border: 2px solid #1a5c38;" + _LED_SIZE,  # BTN0 green border
    "background: #1e1e1e; border: 2px solid #5c1a1a;" + _LED_SIZE,  # BTN1 red border
    "background: #1e1e1e; border: 2px solid #444;"    + _LED_SIZE,  # BTN2 default
    "background: #1e1e1e; border: 2px solid #444;"    + _LED_SIZE,  # BTN3 default
    "background: #1e1e1e; border: 2px solid #444;"    + _LED_SIZE,  # BTN4 default
]

# Per-button flash styles: BTN0=green, BTN1=red, others=orange
_LED_FLASH_STYLES = [
    "background: #00ff88; border: 2px solid #66ffbb;" + _LED_SIZE,  # BTN0 green flash
    "background: #ff3333; border: 2px solid #ff6666;" + _LED_SIZE,  # BTN1 red flash
    "background: #ff8800; border: 2px solid #ffcc00;" + _LED_SIZE,  # BTN2 orange
    "background: #ff8800; border: 2px solid #ffcc00;" + _LED_SIZE,  # BTN3 orange
    "background: #ff8800; border: 2px solid #ffcc00;" + _LED_SIZE,  # BTN4 orange
]

# ---------------------------------------------------------------------------
# TCP receive thread
# ---------------------------------------------------------------------------

class _RemoteTcpThread(threading.Thread):
    """Background thread: opens TCP connection, pushes lines into a queue.

    Queue items: ("connected",) | ("line", str) | ("error", str)
    """

    def __init__(self, host: str, port: int, q: "queue.Queue[tuple]") -> None:
        super().__init__(daemon=True)
        self._host = host
        self._port = port
        self._q    = q
        self._stop = threading.Event()
        self._sock: socket.socket | None = None

    def run(self) -> None:
        try:
            sock = socket.create_connection((self._host, self._port), timeout=5.0)
            sock.settimeout(30.0)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self._sock = sock
            self._q.put(("connected",))
            reader = sock.makefile("r", encoding="ascii", newline="\n")
            while not self._stop.is_set():
                line = reader.readline()
                if line == "":
                    self._q.put(("error", "Connection closed by remote"))
                    return
                line = line.strip()
                if line:
                    self._q.put(("line", line))
        except socket.timeout:
            self._q.put(("error", "Connection timed out"))
        except OSError as exc:
            self._q.put(("error", str(exc)))
        except Exception as exc:
            self._q.put(("error", str(exc)))
        finally:
            self._close_sock()

    def stop(self) -> None:
        self._stop.set()
        self._close_sock()

    def _close_sock(self) -> None:
        try:
            if self._sock is not None:
                self._sock.shutdown(socket.SHUT_RDWR)
                self._sock.close()
                self._sock = None
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class RemoteTestWindow(QtWidgets.QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        self._q: queue.Queue[tuple] = queue.Queue()
        self._thread: _RemoteTcpThread | None = None

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._drain_events)
        self._timer.start(25)

        self._leds: list[QtWidgets.QLabel] = []

        self._build_ui()
        self.setWindowTitle("Remote Button Tester")
        self.resize(500, 580)

    # -----------------------------------------------------------------------
    # UI construction
    # -----------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)
        root.setSpacing(8)
        root.setContentsMargins(10, 10, 10, 10)

        root.addWidget(self._build_connection_group())
        root.addWidget(self._build_buttons_group())
        root.addWidget(self._build_hb_group())
        root.addWidget(self._build_log_group())

    def _build_connection_group(self) -> QtWidgets.QGroupBox:
        gb = QtWidgets.QGroupBox("Connection")
        grid = QtWidgets.QGridLayout(gb)
        grid.setSpacing(6)

        grid.addWidget(QtWidgets.QLabel("IP:"), 0, 0)
        self._txt_ip = QtWidgets.QLineEdit(DEFAULT_IP)
        self._txt_ip.setFixedWidth(130)
        grid.addWidget(self._txt_ip, 0, 1)

        grid.addWidget(QtWidgets.QLabel("Port:"), 0, 2)
        self._txt_port = QtWidgets.QLineEdit(DEFAULT_PORT)
        self._txt_port.setFixedWidth(60)
        grid.addWidget(self._txt_port, 0, 3)

        self._btn_connect = QtWidgets.QPushButton("CONNECT")
        self._btn_connect.setFixedWidth(100)
        self._btn_connect.clicked.connect(self._on_connect)
        grid.addWidget(self._btn_connect, 0, 4)

        self._btn_disconnect = QtWidgets.QPushButton("DISCONNECT")
        self._btn_disconnect.setFixedWidth(100)
        self._btn_disconnect.setEnabled(False)
        self._btn_disconnect.clicked.connect(self._on_disconnect)
        grid.addWidget(self._btn_disconnect, 0, 5)

        grid.setColumnStretch(6, 1)

        self._lbl_status = QtWidgets.QLabel("Status: Disconnected")
        self._lbl_status.setFont(QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold))
        self._set_status("Disconnected", "#888888")
        grid.addWidget(self._lbl_status, 1, 0, 1, 7)

        return gb

    def _build_buttons_group(self) -> QtWidgets.QGroupBox:
        gb = QtWidgets.QGroupBox("Button Status")
        hbox = QtWidgets.QHBoxLayout(gb)
        hbox.setSpacing(16)
        hbox.addStretch()

        for i in range(BTN_COUNT):
            col = QtWidgets.QVBoxLayout()
            col.setSpacing(4)
            col.setAlignment(QtCore.Qt.AlignHCenter)

            led = QtWidgets.QLabel()
            led.setStyleSheet(_LED_IDLE_STYLES[i])
            led.setAlignment(QtCore.Qt.AlignCenter)
            self._leds.append(led)
            col.addWidget(led, alignment=QtCore.Qt.AlignHCenter)

            lbl = QtWidgets.QLabel(_BTN_LABELS[i])
            lbl.setAlignment(QtCore.Qt.AlignHCenter)
            lbl.setFont(QtGui.QFont("Consolas", 8))
            col.addWidget(lbl)

            hbox.addLayout(col)

        hbox.addStretch()
        return gb

    def _build_hb_group(self) -> QtWidgets.QGroupBox:
        gb = QtWidgets.QGroupBox("Heartbeat")
        hbox = QtWidgets.QHBoxLayout(gb)
        self._lbl_hb = QtWidgets.QLabel("Last HB: never")
        self._lbl_hb.setFont(QtGui.QFont("Consolas", 9))
        self._lbl_hb.setStyleSheet("color: #aaaaaa;")
        hbox.addWidget(self._lbl_hb)
        hbox.addStretch()
        return gb

    def _build_log_group(self) -> QtWidgets.QGroupBox:
        gb = QtWidgets.QGroupBox("Log")
        vbox = QtWidgets.QVBoxLayout(gb)
        self._log = QtWidgets.QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QtGui.QFont("Consolas", 9))
        self._log.setMinimumHeight(200)
        vbox.addWidget(self._log)
        return gb

    # -----------------------------------------------------------------------
    # Connection management
    # -----------------------------------------------------------------------

    def _on_connect(self) -> None:
        host = self._txt_ip.text().strip()
        try:
            port = int(self._txt_port.text().strip())
        except ValueError:
            QtWidgets.QMessageBox.critical(self, "Error", "Port must be a number.")
            return

        self._set_status("Connecting...", "#f39c12")
        self._q = queue.Queue()
        self._thread = _RemoteTcpThread(host, port, self._q)
        self._thread.start()
        self._btn_connect.setEnabled(False)

    def _on_disconnect(self) -> None:
        self._cleanup_thread()
        self._set_status("Disconnected", "#888888")
        self._btn_connect.setEnabled(True)
        self._btn_disconnect.setEnabled(False)

    def _cleanup_thread(self) -> None:
        if self._thread is not None:
            self._thread.stop()
            self._thread = None

    # -----------------------------------------------------------------------
    # Event drain (25 ms timer)
    # -----------------------------------------------------------------------

    def _drain_events(self) -> None:
        while True:
            try:
                item = self._q.get_nowait()
            except queue.Empty:
                break

            kind = item[0]

            if kind == "connected":
                self._btn_disconnect.setEnabled(True)
                self._append_log("=== Connected ===")

            elif kind == "error":
                self._set_status(f"Error: {item[1]}", "#c0392b")
                self._append_log(f"[ERROR] {item[1]}")
                self._cleanup_thread()
                self._btn_connect.setEnabled(True)
                self._btn_disconnect.setEnabled(False)

            elif kind == "line":
                line: str = item[1]
                self._append_log(line)
                self._handle_line(line)

    def _handle_line(self, line: str) -> None:
        if line.startswith("BTN:"):
            try:
                idx = int(line[4:].strip())
                if 0 <= idx < BTN_COUNT:
                    self._flash_led(idx)
            except ValueError:
                pass

        elif line == "HB":
            now = datetime.datetime.now().strftime("%H:%M:%S")
            self._lbl_hb.setText(f"Last HB: {now}")
            self._lbl_hb.setStyleSheet("color: #27ae60;")

        elif line.startswith("HELLO:"):
            self._set_status(f"Connected — {line}", "#27ae60")

        elif line.startswith("ERR:"):
            self._set_status(f"Error: {line}", "#c0392b")

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _flash_led(self, idx: int) -> None:
        self._leds[idx].setStyleSheet(_LED_FLASH_STYLES[idx])
        QtCore.QTimer.singleShot(400, lambda i=idx: self._leds[i].setStyleSheet(_LED_IDLE_STYLES[i]))

    def _set_status(self, text: str, color: str) -> None:
        self._lbl_status.setText(f"Status: {text}")
        self._lbl_status.setStyleSheet(f"color: {color};")

    def _append_log(self, text: str) -> None:
        self._log.append(text)
        # Keep log bounded at 200 lines
        doc = self._log.document()
        while doc.blockCount() > 200:
            cursor = QtGui.QTextCursor(doc.begin())
            cursor.select(QtGui.QTextCursor.BlockUnderCursor)
            cursor.movePosition(QtGui.QTextCursor.NextCharacter,
                                QtGui.QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
        self._log.verticalScrollBar().setValue(self._log.verticalScrollBar().maximum())

    # -----------------------------------------------------------------------
    # Window close
    # -----------------------------------------------------------------------

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self._timer.stop()
        self._cleanup_thread()
        event.accept()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    win = RemoteTestWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
