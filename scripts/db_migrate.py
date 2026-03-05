import subprocess
import sys


def main() -> int:
    cmd = ["alembic", "-c", "apps/api/alembic.ini", "upgrade", "head"]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
