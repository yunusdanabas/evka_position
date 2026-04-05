import threading
import unittest

import numpy as np

from tools.position_checker.data_store import DataStore
from tools.position_checker.parser import ParsedFrame


def mk_frame(i: int) -> ParsedFrame:
    return ParsedFrame(
        x_mm=float(i),
        y_mm=float(i + 1),
        z_mm=float(i + 2),
        r_mm=float(i + 3),
        theta_deg=float(i + 4),
        phi_deg=float(i + 5),
        is_valid=1,
        frame_count=i,
        ts_ms=i * 10,
    )


class DataStoreTests(unittest.TestCase):
    def test_ring_buffer_maxlen(self) -> None:
        store = DataStore(maxpoints=3)
        for i in range(10):
            store.push(mk_frame(i))

        snap = store.snapshot()
        self.assertEqual(len(snap), 3)
        self.assertEqual([f.frame_count for f in snap], [7, 8, 9])

    def test_threaded_push_and_snapshot(self) -> None:
        store = DataStore(maxpoints=50)

        def worker(start: int) -> None:
            for j in range(start, start + 200):
                store.push(mk_frame(j))

        threads = [threading.Thread(target=worker, args=(k * 1000,)) for k in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        snap = store.snapshot()
        self.assertLessEqual(len(snap), 50)
        self.assertIsNotNone(store.latest())

    def test_transform_preserves_firmware_spherical_values(self) -> None:
        store = DataStore(maxpoints=5)
        store.set_transform(np.eye(3, dtype=float), np.array([10.0, 0.0, 0.0], dtype=float))

        frame = ParsedFrame(
            x_mm=1.0,
            y_mm=2.0,
            z_mm=3.0,
            r_mm=111.0,
            theta_deg=22.0,
            phi_deg=-33.0,
            is_valid=1,
            frame_count=1,
            ts_ms=10,
        )
        store.push(frame)
        latest = store.latest()
        self.assertIsNotNone(latest)
        self.assertAlmostEqual(latest.x_mm, 11.0)
        self.assertAlmostEqual(latest.r_mm, 111.0)
        self.assertAlmostEqual(latest.theta_deg, 22.0)
        self.assertAlmostEqual(latest.phi_deg, -33.0)


if __name__ == "__main__":
    unittest.main()
