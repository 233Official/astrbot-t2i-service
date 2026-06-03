from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    smoke_script = Path(__file__).resolve().parents[1] / "scripts" / "render_smoke.py"
    return subprocess.call([sys.executable, str(smoke_script), *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
