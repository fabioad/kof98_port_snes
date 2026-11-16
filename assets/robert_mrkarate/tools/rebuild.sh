#!/usr/bin/env bash
set -e
cd -- "$(dirname -- "$0")/.."
python3 tools/build_mrkarate.py
python3 tools/build_moves.py
python3 tools/package_variant.py
