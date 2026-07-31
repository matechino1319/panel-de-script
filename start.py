import subprocess
import sys
import time
import webbrowser
from pathlib import Path


PORT = 5050
BASE_DIR = Path(__file__).resolve().parent


def install_dependencies():
    packages = ["flask", "pandas", "openpyxl", "werkzeug"]
    subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])


def run_server():
    url = f"http://127.0.0.1:{PORT}"
    webbrowser.open(url)
    subprocess.run([sys.executable, "app.py"], cwd=str(BASE_DIR))


if __name__ == "__main__":
    try:
        install_dependencies()
        run_server()
    except KeyboardInterrupt:
        pass
