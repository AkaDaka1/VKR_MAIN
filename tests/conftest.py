import os
import sys

# Корень проекта в PYTHONPATH для импорта backend.*
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
