"""test_tcp_client.py — unit tests for TcpClient."""

import socket
import threading
import time
import unittest

from tools.position_checker.tcp_client import TcpClient


class _LineServer:
    """TCP server that sends one line after connect."""

    def __init__(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(1)
        self.port = self._sock.getsockname()[1]
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        self._sock.settimeout(0.5)
        while not self._stop.is_set():
            try:
                conn, _ = self._sock.accept()
            except socket.timeout:
                continue
            conn.settimeout(2.0)
            try:
                conn.sendall(b"X0.00,Y0.00,Z0.00\n")
                time.sleep(0.05)
            finally:
                conn.close()

    def close(self) -> None:
        self._stop.set()
        self._sock.close()


class TcpClientTests(unittest.TestCase):
    def test_not_connected_send_fails(self) -> None:
        client = TcpClient()
        ok, info = client.send_command("PING")
        self.assertFalse(ok)
        self.assertIn("not connected", info.lower())

    def test_connect_receive_and_close(self) -> None:
        server = _LineServer()
        try:
            client = TcpClient()
            received: list[str] = []
            client.set_callbacks(on_line=lambda line: received.append(line))
            ok, _ = client.connect("127.0.0.1", server.port, timeout_s=2.0, io_timeout_s=2.0)
            self.assertTrue(ok)
            self.assertTrue(client.is_connected())
            deadline = time.time() + 2.0
            while time.time() < deadline and not received:
                time.sleep(0.05)
            self.assertTrue(received)
            self.assertTrue(received[0].startswith("X"))
            client.close(emit_disconnect=False)
            self.assertFalse(client.is_connected())
        finally:
            server.close()

    def test_close_idempotent(self) -> None:
        client = TcpClient()
        client.close(emit_disconnect=False)
        client.close(emit_disconnect=False)


if __name__ == "__main__":
    unittest.main()
