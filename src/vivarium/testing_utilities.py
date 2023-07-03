"""
==========================
Vivarium Testing Utilities
==========================

Utility functions and classes to make testing ``vivarium`` components easier.

"""
from pathlib import Path


def metadata(file_path):
    return {"layer": "override", "source": str(Path(file_path).resolve())}
