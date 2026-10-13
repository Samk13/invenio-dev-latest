#!/usr/bin/env python3
"""Generate a ZIP containing N ZIP files to test Invenio's preview entry limit.

Example:
    python3 scripts/dev/generate_nested_zip.py --count 41951 --output "My_Large_File.zip"

Upload the result to a record and open its ZIP preview. With a 10,000-entry
limit, counts above 10,000 should trigger the "Too many files in ZIP" error.
The count refers to entries in the outer ZIP, not recursively nested contents.
This generates a small test fixture, not a decompression bomb.
"""

import argparse
import io
from pathlib import Path
import zipfile


def positive_int(value):
    """Parse a positive archive entry count."""
    count = int(value)
    if count < 1:
        raise argparse.ArgumentTypeError("count must be greater than zero")
    return count


def main():
    """Write a valid outer ZIP with exactly the requested number of entries."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-n",
        "--count",
        type=positive_int,
        default=41951,
        help="number of inner ZIP files (default: 41951)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("My_Large_File.zip"),
        help="output path (default: My_Large_File.zip); must not already exist",
    )
    args = parser.parse_args()

    # Reuse a valid, tiny archive to avoid retaining N payloads in memory.
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as inner:
        inner.writestr("hello.txt", b"ZIP preview entry-limit test.\n")
    payload = buffer.getvalue()

    try:
        # Exclusive creation protects existing files. Stored entries avoid
        # introducing compression-ratio limits into this entry-count test.
        with zipfile.ZipFile(args.output, "x", compression=zipfile.ZIP_STORED) as outer:
            for index in range(1, args.count + 1):
                outer.writestr(f"inner_{index:06d}.zip", payload)
    except FileExistsError:
        parser.error(f"output already exists: {args.output}")

    print(
        f"Created {args.output}: {args.count:,} inner ZIPs, {args.output.stat().st_size:,} bytes"
    )
    if args.count <= 10000:
        print("Note: use --count 10001 or higher to exceed a 10,000-entry limit.")


if __name__ == "__main__":
    main()
