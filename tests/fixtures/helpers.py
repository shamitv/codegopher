from __future__ import annotations

import shutil
from pathlib import Path


PROJECT_FIXTURES = Path(__file__).parent / "projects"


def copy_project_fixture(name: str, destination_root: Path) -> Path:
    source = PROJECT_FIXTURES / name
    if not source.is_dir():
        raise FileNotFoundError(f"Unknown fixture project: {name}")
    destination = destination_root / name
    shutil.copytree(source, destination)
    return destination

