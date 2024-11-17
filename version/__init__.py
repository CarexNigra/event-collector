import tomllib
from functools import lru_cache
from pathlib import Path


@lru_cache
def get_version_from_pyproject():
    current_dir = Path(__file__).parent
    pyproject_path = current_dir.parent / "pyproject.toml"
    try:
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)
        version = pyproject_data.get("tool", {}).get("poetry", {}).get("version")
        if not version:
            raise KeyError("Version field not found in pyproject.toml")
        return version
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve version: {e}")
