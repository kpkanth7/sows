import os
import sys

# Scripts use bare imports (e.g. `from db import ...`), so put scripts/ on the path.
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
