"""
CLI entry point: ``python -m scarp_offset <profile_file>``
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="scarp_offset",
        description=(
            "Measure vertical surface offset across a fault scarp from a "
            "topographic profile.  Interactive matplotlib GUI guides you "
            "through surface selection."
        ),
    )
    parser.add_argument(
        "profile",
        type=Path,
        help=(
            "Path to a two-column text file (horizontal distance, elevation). "
            "Supports .txt, .dat, and .csv.  Comment lines starting with "
            "'%%' or '#' are ignored."
        ),
    )
    parser.add_argument(
        "--batch",
        nargs="*",
        type=Path,
        metavar="FILE",
        help="Additional profile files to process sequentially.",
    )

    args = parser.parse_args(argv)
    files = [args.profile] + (args.batch or [])

    # Deferred import so --help is fast
    from scarp_offset.interactive import ScarpSession

    for fpath in files:
        if not fpath.exists():
            print(f"Error: file not found — {fpath}", file=sys.stderr)
            continue
        print(f"\n{'='*60}")
        print(f"  Processing: {fpath.name}")
        print(f"{'='*60}")
        session = ScarpSession(fpath)
        session.run()


if __name__ == "__main__":
    main()
