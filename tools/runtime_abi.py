"""Shared constants for the 65816 engine and its measurement tools."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ABI = json.loads((ROOT / 'assets/runtime_abi.json').read_text())

def emit(root=ROOT, out_dir=None):
    # The experimental HI build generates into its own tree; every other
    # caller keeps the historical build/gen_fight location.
    base = Path(out_dir) if out_dir is not None else Path(root) / 'build/gen_fight'
    target = base / 'runtime_abi.inc'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('; generated from assets/runtime_abi.json\n' + ''.join(
        f'.DEFINE {key} {value}\n' for key, value in ABI.items()
        if not key.startswith('F_')))

if __name__ == '__main__':
    emit()
