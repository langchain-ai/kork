"""Get the version of the package."""
from importlib import metadata

try:
    __version__ = metadata.version("kork")
except metadata.PackageNotFoundError:
    __version__ = "local"
