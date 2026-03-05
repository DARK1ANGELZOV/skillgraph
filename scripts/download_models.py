import subprocess
import sys


def main() -> int:
    cmd = [sys.executable, "services/ai/scripts/download_models.py"]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
