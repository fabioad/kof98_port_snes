#!/usr/bin/env bash
set -e
cd -- "$(dirname -- "$0")/ikemen-test"
exec ./Ikemen_GO_Linux -p1 Robert-KOF98/Robert-Mr-Karate.def -p2 kfm -s stages/stage0.def -p1.ai 0 -p2.ai 0 -p1.power 3000
