#!/bin/bash

# Usage: ./split_bin.sh mydata.parquet 50
# This splits mydata.parquet into 50MB chunks and saves mydata.parquet.md5sum

set -e

FILE="$1"
CHUNK_SIZE_MB="$2"

if [[ -z "$FILE" || -z "$CHUNK_SIZE_MB" ]]; then
  echo "Usage: $0 <file.parquet> <chunk_size_mb>"
  exit 1
fi

BASENAME=$(basename "$FILE")
DIRNAME=$(dirname "$FILE")

# Generate md5sum
md5sum "$FILE" | awk '{print $1}' > "$FILE.md5sum"

# Split file
split --bytes="${CHUNK_SIZE_MB}M" --numeric-suffixes=1 --suffix-length=3 "$FILE" "$FILE.part."

echo "Split complete. Chunks saved as $FILE.part.### and MD5 saved as $FILE.md5sum"