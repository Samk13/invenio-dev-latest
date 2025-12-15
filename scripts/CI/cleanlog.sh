#!/bin/sh

# Usage:
# cleanlog.sh input_file [-o output_file] [-p "pattern1|pattern2|pattern3"]
# Removes lines matching any of the specified patterns (case insensitive)
# usful for cleaning build logs from known warnings where GH UI cannot load long logs. 

DEFAULT_PATTERNS="is deprecated|method is considered legacy|warning"

INPUT=""
OUTPUT=""
PATTERNS="$DEFAULT_PATTERNS"

while getopts ":o:p:" opt; do
  case "$opt" in
    o) OUTPUT="$OPTARG" ;;
    p) PATTERNS="$OPTARG" ;;
    *) echo "Usage: $0 input_file [-o output_file] [-p \"pattern1|pattern2\"]"
       exit 1 ;;
  esac
done

shift $((OPTIND - 1))
INPUT="$1"

if [ -z "$INPUT" ]; then
  echo "Input file required"
  exit 1
fi

if [ -z "$OUTPUT" ]; then
  DIR="$(dirname "$INPUT")"
  BASE="$(basename "$INPUT")"
  OUTPUT="$DIR/clean-$BASE"
fi

grep -vi -E "$PATTERNS" "$INPUT" > "$OUTPUT"

echo "$OUTPUT"
