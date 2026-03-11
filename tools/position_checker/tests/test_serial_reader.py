import unittest
from unittest.mock import patch

from tools.position_checker.data_store import DataStore
from tools.position_checker.serial_reader import SerialReader
import tools.position_checker.serial_reader as serial_reader_module


class _FakeSerialPort:
    def __init__(self, lines, reader: SerialReader):
        self._lines = list(lines)
        self._reader = reader
        self.is_open = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.is_open = False
        return False

    def readline(self):
        if self._lines:
            return self._lines.pop(0)
        self._reader.stop()
        return b""

    def write(self, _payload):
        return 0


class SerialReaderTests(unittest.TestCase):
    def test_reconnect_then_read_data(self) -> None:
        store = DataStore(maxpoints=20)
        reader = SerialReader(
            port="FAKE_PORT",
            baud=115200,
            store=store,
            reconnect=True,
            reconnect_interval=0.01,
        )

        calls = {"count": 0}

        def fake_serial_ctor(*_args, **_kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                raise serial_reader_module.serial.SerialException("open fail")
            return _FakeSerialPort(
                [
                    b"ACK:PONG\n",
                    b"DATA,1.0,2.0,3.0,4.0,5.0,6.0,1,11,22\n",
                ],
                reader,
            )

        with patch(
            "tools.position_checker.serial_reader.serial.Serial",
            side_effect=fake_serial_ctor,
        ):
            reader.start()
            reader.join(timeout=1.5)
            reader.stop()
            reader.join(timeout=0.5)

        self.assertFalse(reader.is_alive())
        self.assertGreaterEqual(calls["count"], 2)
        self.assertEqual(len(store.snapshot()), 1)
        status = store.get_runtime_status()
        self.assertIn("ACK:PONG", str(status["last_info"]))


if __name__ == "__main__":
    unittest.main()
