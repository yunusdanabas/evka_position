import tempfile
import unittest
from pathlib import Path

from tools.position_checker.replay_reader import load_replay_frames


class ReplayReaderTests(unittest.TestCase):
    def test_missing_replay_file_returns_empty_list(self) -> None:
        missing = Path("/tmp") / "evka_position_missing_replay_file.csv"
        if missing.exists():
            missing.unlink()
        self.assertEqual(load_replay_frames(str(missing)), [])

    def test_load_raw_data_dump(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "raw_dump.txt"
            path.write_text(
                "DATA,1.0,2.0,3.0,4.0,5.0,6.0,1,7,8\n"
                "ACK:PONG\n"
                "DATA,bad,row\n",
                encoding="utf-8",
            )
            frames = load_replay_frames(str(path))
            self.assertEqual(len(frames), 1)
            self.assertEqual(frames[0].frame_count, 7)


if __name__ == "__main__":
    unittest.main()
