#!/bin/bash

# Usage: ./reassemble_parquet.sh mydata.parquet
# If mydata.parquet exists, verify MD5 only.
# If it doesn't, reassemble from parts and verify MD5.

set -e

FILE="$1"

if [[ -z "$FILE" ]]; then
  echo "Usage: $0 <file.parquet>"
  exit 1
fi

MD5_FILE="${FILE}.md5sum"

if [[ ! -f "$MD5_FILE" ]]; then
  echo "❌ Missing MD5 file: $MD5_FILE"
  exit 1
fi

EXPECTED=$(cat "$MD5_FILE")

if [[ -f "$FILE" ]]; then
  echo "ℹ️ $FILE already exists. Verifying MD5..."
else
  echo "🔧 Reassembling $FILE from parts..."
  cat "$FILE".part.* > "$FILE"
fi

ACTUAL=$(md5sum "$FILE" | awk '{print $1}')

if [[ "$EXPECTED" == "$ACTUAL" ]]; then
  echo "✅ MD5 match."
else
  echo "❌ MD5 mismatch!"
  echo "Expected: $EXPECTED"
  echo "Actual:   $ACTUAL"
  exit 1
fi