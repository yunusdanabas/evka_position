"""serial_reader.py — daemon thread that reads the serial port and fills DataStore."""

import threading

import serial  # type: ignore

from .data_store import DataStore
from .parser import parse_line


class SerialReader(threading.Thread):
    """Background daemon thread: reads lines, parses DATA frames, pushes to store."""

    def __init__(self, port: str, baud: int, store: DataStore):
        super().__init__(daemon=True, name="serial-reader")
        self._port = port
        self._baud = baud
        self._store = store
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        try:
            with serial.Serial(self._port, self._baud, timeout=1) as ser:
                # Share the open port with the DataStore so it can send commands
                self._store._ser = ser
                print(f"[SerialReader] Connected to {self._port} @ {self._baud}")
                while not self._stop_event.is_set():
                    try:
                        raw = ser.readline()
                        if not raw:
                            continue
                        line = raw.decode("utf-8", errors="replace")
                        frame = parse_line(line)
                        if frame is not None:
                            self._store.push(frame)
                    except serial.SerialException as exc:
                        print(f"[SerialReader] Serial error: {exc}")
                        break
        except serial.SerialException as exc:
            print(f"[SerialReader] Cannot open {self._port}: {exc}")
