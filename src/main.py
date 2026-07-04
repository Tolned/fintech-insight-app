import sys
from pathlib import Path

from src.views import run_app

sys.path.append("A:\\Project\\fintech-insight-app")

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main() -> None:
    run_app()


if __name__ == "__main__":  # pragma: no cover
    main()
