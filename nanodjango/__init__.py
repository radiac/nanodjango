import pluggy

from .defer import defer

# Register pluggy hook
hookimpl = pluggy.HookimplMarker("nanodjango")

__version__ = "0.13.0"
__all__ = ["Django", "defer", "hookimpl"]

# Lazy loading for Django class
# This ensures configure_early() runs when the user's script imports Django,
# not when nanodjango is first imported (important for CLI mode)
_Django = None


def __getattr__(name: str):
    global _Django
    if name == "Django":
        if _Django is None:
            from .early import configure_early

            configure_early()
            from .app import Django

            _Django = Django
        return _Django
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
