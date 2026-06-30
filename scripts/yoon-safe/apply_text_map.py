from __future__ import annotations

import argparse

from hwpx_safe_edit import apply_text_map, path_arg, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply text-node replacements to a copied HWPX.")
    parser.add_argument("--source", required=True, type=path_arg, help="Source HWPX. This file is never modified in place.")
    parser.add_argument("--map", required=True, dest="map_path", type=path_arg, help="JSON replacement map.")
    parser.add_argument("--output", required=True, type=path_arg, help="Output HWPX path.")
    parser.add_argument("--keep-linesegarray", action="store_true", help="Do not remove hp:linesegarray after text replacement.")
    parser.add_argument("--json", type=path_arg, default=None, help="Write JSON summary to this path instead of stdout.")
    args = parser.parse_args()
    summary = apply_text_map(args.source, args.map_path, args.output, remove_linesegarray=not args.keep_linesegarray)
    write_json(summary, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
