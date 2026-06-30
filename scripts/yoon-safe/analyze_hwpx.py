from __future__ import annotations

import argparse

from hwpx_safe_edit import add_common_json_arg, analyze_hwpx, path_arg, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze HWPX ZIP/XML structure.")
    parser.add_argument("hwpx", type=path_arg)
    add_common_json_arg(parser)
    args = parser.parse_args()
    write_json(analyze_hwpx(args.hwpx), args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
