import pluggy

from .app import Django
from .defer import defer

# Register pluggy hook
hookimpl = pluggy.HookimplMarker("nanodjango")

__version__ = "0.18.0"
__all__ = ["Django", "defer", "hookimpl"]
