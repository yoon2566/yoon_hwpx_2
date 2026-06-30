from __future__ import annotations

import argparse

from hwpx_safe_edit import path_arg, validate_hwpx, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate HWPX package and safe-edit expectations.")
    parser.add_argument("hwpx", type=path_arg)
    parser.add_argument("--must-contain", action="append", default=[], help="Text that must exist in section XML.")
    parser.add_argument("--must-not-contain", action="append", default=[], help="Text that must not exist in section XML.")
    parser.add_argument("--expect-no-linesegarray", action="store_true")
    parser.add_argument("--json", type=path_arg, default=None, help="Write JSON report to this path instead of stdout.")
    args = parser.parse_args()
    report = validate_hwpx(
        args.hwpx,
        must_contain=args.must_contain,
        must_not_contain=args.must_not_contain,
        expect_no_linesegarray=args.expect_no_linesegarray,
    )
    write_json(report, args.json)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
