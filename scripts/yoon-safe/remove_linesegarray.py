from __future__ import annotations

import argparse

from hwpx_safe_edit import path_arg, remove_linesegarray_from_hwpx, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove hp:linesegarray from all HWPX section XML files.")
    parser.add_argument("source", type=path_arg)
    parser.add_argument("output", type=path_arg)
    parser.add_argument("--json", type=path_arg, default=None, help="Write JSON summary to this path instead of stdout.")
    args = parser.parse_args()
    write_json(remove_linesegarray_from_hwpx(args.source, args.output), args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
