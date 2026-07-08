"""Entry point: launch the Quick IPT GUI.

    python -m tools.ipt --tcp 192.168.1.50:8080
    python -m tools.ipt --serial /dev/ttyUSB0 --baud 115200

With no transport flag the GUI opens disconnected; pick TCP/serial in the panel.
"""
import argparse
import sys

from .gui import run_ipt_gui


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="tools.ipt", description="EVKA Quick IPT")
    ap.add_argument("--tcp", metavar="HOST:PORT",
                    help="connect over TCP to the CMD server (e.g. 192.168.1.50:8080)")
    ap.add_argument("--serial", metavar="PORT", help="serial device (e.g. /dev/ttyUSB0)")
    ap.add_argument("--baud", type=int, default=115200, help="serial baud (default 115200)")
    args = ap.parse_args(argv)

    tcp = None
    if args.tcp:
        host, _, port = args.tcp.partition(":")
        tcp = (host, int(port) if port else 8080)
    serial = (args.serial, args.baud) if args.serial else None
    return run_ipt_gui(tcp=tcp, serial=serial)


if __name__ == "__main__":
    sys.exit(main())
