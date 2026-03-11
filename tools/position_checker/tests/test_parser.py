import unittest

from tools.position_checker.parser import parse_info_line, parse_line


class ParserTests(unittest.TestCase):
    def test_parse_valid_data_line(self) -> None:
        frame = parse_line("DATA,1.0,2.0,3.0,4.0,5.0,6.0,1,7,8\n")
        self.assertIsNotNone(frame)
        self.assertEqual(frame.x_mm, 1.0)
        self.assertEqual(frame.frame_count, 7)
        self.assertEqual(frame.ts_ms, 8)

    def test_parse_invalid_data_line(self) -> None:
        self.assertIsNone(parse_line("DATA,1,2,3\n"))
        self.assertIsNone(parse_line("DATA,a,b,c,d,e,f,g,h,i\n"))

    def test_parse_info_line(self) -> None:
        self.assertEqual(parse_info_line("ACK:PONG\n"), "ACK:PONG")
        self.assertEqual(parse_info_line("STATUS,1,10,500\n"), "STATUS,1,10,500")
        self.assertIsNone(parse_info_line("Cartesian: X=1"))


if __name__ == "__main__":
    unittest.main()
