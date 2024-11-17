import tomllib
from functools import lru_cache
from pathlib import Path


@lru_cache
def get_version_from_pyproject():
    """
    Function dynamically retrievies the project's version from its metadata, 
    ensuring consistency across the application and its dependencies.

    Returns:
        A string representing the project version, as specified in the tool.poetry.version 
        field of the pyproject.toml file.

    Raises:
        RuntimeError: If the function fails to read the file, parse its content, or find the version field.
        KeyError: Raised internally if the version field is missing (wrapped in RuntimeError).
    """
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
