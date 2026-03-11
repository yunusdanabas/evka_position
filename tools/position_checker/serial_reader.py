"""serial_reader.py — daemon thread that reads the serial port and fills DataStore."""

import threading

import serial  # type: ignore

from .data_store import DataStore
from .parser import parse_info_line, parse_line


class SerialReader(threading.Thread):
    """Background daemon thread: reads lines, parses DATA frames, pushes to store."""

    def __init__(
        self,
        port: str,
        baud: int,
        store: DataStore,
        reconnect: bool = True,
        reconnect_interval: float = 1.0,
    ):
        super().__init__(daemon=True, name="serial-reader")
        self._port = port
        self._baud = baud
        self._store = store
        self._reconnect = reconnect
        self._reconnect_interval = max(0.1, reconnect_interval)
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        base_retry_s = self._reconnect_interval
        backoff_s = base_retry_s

        while not self._stop_event.is_set():
            try:
                with serial.Serial(self._port, self._baud, timeout=0.2) as ser:
                    self._store.set_serial(ser)
                    self._store.set_connection(True, f"Connected: {self._port} @ {self._baud}")
                    self._store.set_error("")
                    backoff_s = base_retry_s
                    print(f"[SerialReader] Connected to {self._port} @ {self._baud}")

                    while not self._stop_event.is_set():
                        raw = ser.readline()
                        if not raw:
                            continue

                        line = raw.decode("utf-8", errors="replace")
                        frame = parse_line(line)
                        if frame is not None:
                            self._store.push(frame)
                            continue

                        info = parse_info_line(line)
                        if info is not None:
                            self._store.set_info(info)
                            print(f"[SerialReader] {info}")

            except serial.SerialException as exc:
                msg = f"Serial error: {exc}"
                self._store.set_error(msg)
                self._store.set_connection(False, msg)
                self._store.set_serial(None)
                print(f"[SerialReader] {msg}")

                if not self._reconnect or self._stop_event.is_set():
                    break

                # Exponential backoff capped at 5 s.
                self._stop_event.wait(backoff_s)
                backoff_s = min(backoff_s * 1.5, 5.0)
                continue
            finally:
                self._store.set_serial(None)
                if not self._stop_event.is_set():
                    self._store.set_connection(False, "Disconnected")

            if not self._reconnect:
                break

        self._store.set_connection(False, "Stopped")
