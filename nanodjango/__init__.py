import pluggy

from .app import Django

# Register pluggy hook
hookimpl = pluggy.HookimplMarker("nanodjango")


__version__ = "0.10.0"
__all__ = ["Django", "hookimpl"]
