#!/usr/bin/env bash
# Remove all lines starting with an ISO timestamp and containing "warning"

# Check arguments
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <input_file> [output_file]"
  exit 1
fi

input_file="$1"
output_file="${2:-cleaned.txt}"  # default output if none given

# Run the grep filter
grep -viE '^[0-9]{4}-[0-9]{2}-[0-9]{2}T.*warning' "$input_file" > "$output_file"

echo "✅ Cleaned file written to: $output_file"
