from __future__ import annotations

import argparse

from hwpx_safe_edit import extract_text_map, path_arg, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract HWPX hp:t text nodes to JSON.")
    parser.add_argument("hwpx", type=path_arg)
    parser.add_argument("--section", action="append", default=None, help="Section entry to inspect, e.g. Contents/section0.xml.")
    parser.add_argument("--output", type=path_arg, default=None, help="Output JSON path.")
    args = parser.parse_args()
    write_json(extract_text_map(args.hwpx, args.section), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
