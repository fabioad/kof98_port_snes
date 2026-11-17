#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
engine_dir='/run/media/fabio/Dados/Fabio/Ikemen_GO-dev-linux'
test_dir="$(mktemp -d /tmp/sakura-ikemen.XXXXXX)"
for item in "$engine_dir"/*; do
    name="${item##*/}"
    case "$name" in
        data|save) cp -a -- "$item" "$test_dir/$name" ;;
        *) ln -s -- "$item" "$test_dir/$name" ;;
    esac
done
cd -- "$test_dir"
exec ./Ikemen_GO_Linux \
    -p1 "$project_dir/Sakura-KOF98.def" -p1.color 4 \
    -p2 '/run/media/fabio/Dados/Fabio/kof98_port_snes/assets/characters/Kyo-KOF98/Kyo-KOF98.def' \
    -s stages/KOF98-JpnStreetStage.def \
    -windowed -width 960 -height 720 -nojoy -nomusic -time -1 "$@"
