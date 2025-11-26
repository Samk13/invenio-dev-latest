import json
import sys
from pathlib import Path

def csv_to_json(csv_path: str, json_path: str):
    csv_file = Path(csv_path)
    if not csv_file.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)

    output = {}

    with csv_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # split at first comma
            if "," not in line:
                print(f"Warning: skipping malformed line: {line}")
                continue
            pkg, versions = line.split(",", 1)

            # clean versions
            versions = (
                versions.replace("=", "")     # remove '='
                        .replace("||", ",")   # replace "||" with ","
                        .replace(" ", "")     # remove spaces
                        .strip()
            )

            output[pkg] = versions

    # Write JSON file
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(output, json_file, indent=2)
    print(f"JSON written to: {json_path}")



if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert.py <input.csv> <output.json>")
        sys.exit(1)
    csv_to_json(sys.argv[1], sys.argv[2])
