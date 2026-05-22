import os
from pathlib import Path


def get_repo_root():
    return Path(__file__).resolve().parent


def get_data_dir():
    override = os.environ.get("PY_OS_DATA_DIR")
    if override:
        return override
    return str(get_repo_root() / ".py-os-data")
