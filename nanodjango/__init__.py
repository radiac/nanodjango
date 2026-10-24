import pluggy

from .app import Django
from .defer import defer

# Register pluggy hook
hookimpl = pluggy.HookimplMarker("nanodjango")

__version__ = "0.16.4"
__all__ = ["Django", "defer", "hookimpl"]
