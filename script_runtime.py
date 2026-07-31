import glob
import os
from pathlib import Path


def get_input_dir(default=None):
    return os.environ.get("SCRIPT_INPUT_DIR", default or os.getcwd())


def get_output_dir(default=None):
    path = os.environ.get("SCRIPT_OUTPUT_DIR", default or os.getcwd())
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def get_input_file():
    path = os.environ.get("SCRIPT_INPUT_FILE", "").strip()
    if path and os.path.exists(path):
        return path
    return None


def find_files(patterns, directory=None):
    base_dir = directory or get_input_dir()
    found = []
    for pattern in patterns:
        found.extend(glob.glob(os.path.join(base_dir, pattern)))

    filtered = []
    seen = set()
    for path in found:
        name = os.path.basename(path)
        normalized = os.path.abspath(path).lower()
        if normalized in seen:
            continue
        if name.startswith("~$"):
            continue
        seen.add(normalized)
        filtered.append(path)

    filtered.sort(key=os.path.getmtime, reverse=True)
    return filtered
