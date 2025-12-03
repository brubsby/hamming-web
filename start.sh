#!/usr/bin/env bash
PHRASE="${1:-Tyler Typical}"
DEPTH="${2:-2}"

echo "Generating graph for '$PHRASE' with depth $DEPTH..."
uv run main.py "$PHRASE" --depth "$DEPTH" --json graph.json

echo "Starting server at http://localhost:8000"
python3 -m http.server 8000
