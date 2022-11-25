import re
import sys
from pathlib import Path

from setuptools import setup


def find_version(*paths):
    path = Path(*paths)
    content = path.read_text()
    match = re.search(r"^__version__\s*=\s*['\"]([^'\"]*)['\"]", content, re.M)
    if match:
        return match.group(1)
    raise RuntimeError("Unable to find version string.")


# Setup unless this is being imported by Sphinx, which just wants find_version
if "sphinx" not in sys.modules:
    setup(version=find_version("django_flasky", "__init__.py"))
