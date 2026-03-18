import os
import sys


def get_resource_path(relative_path: str) -> str:
    """
    Resolve the absolute path to a bundled resource file.

    - In development: resolved relative to the project root directory.
    - In a PyInstaller bundle (--onefile or --onedir): resolved from
      sys._MEIPASS, where PyInstaller extracts bundled data files at runtime.
    """
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        # utils/ is one level below the project root
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)
