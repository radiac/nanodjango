"""
Helpers to modify settings without defining custom callables

Usage:

    from nanodjango import Setting

    app = Django(
        # Collect a setting from the environment (os.getenv convenience wrapper)
        BAR=Django.conf.env("BAR", "default_value"),

        # Add values to a list
        INSTALLED_APPS=Django.conf.append("django_tagulous"),

        # Set dict items
        STORAGES=Django.conf(archive={...}),  # STORAGES["archive"] = {...}

        # Remove a value from a list (or a key from a dict)
        SOME_LIST=Django.conf.remove("foo")  # removes the value "foo"
        SOME_DICT=Django.conf.remove("bar")  # removes the key "bar"

        # Pass multiple modifiers into Django.conf() to chain them
        OTHER_LIST=Django.conf(
            Django.conf.append("foo"),
            Django.conf.remove("bar"),
        ),

        # Nest Django.conf to modify complex objects
        # * modify a list index by passing the keyword _INDEX, eg first item is _0
        # * modify dict settings by passing the key as a a keyword
        TEMPLATES = Django.conf(
            _0=Django.conf(
                OPTIONS=Django.conf(
                    context_processors=Django.conf.append(
                        "myscript.template_context",
                    ),
                ),
            ),
        )

        # But this can be written more neatly using the __ syntax (expanded internally)
        TEMPLATES__0__OPTIONS__context_processors = Django.conf.append(
            "myscript.template_context",
        )
    )
"""

from __future__ import annotations

from os import getenv
from typing import Any, Callable


class ModifierError(Exception):
    """
    Exception raised when a modifier fails to apply to a setting.

    Tracks the path through nested settings to provide helpful error messages.
    """

    def __init__(self, msg: str, attr: Any = None):
        self.msg = msg
        self.path: list[Any] = []
        if attr is not None:
            self.path.append(attr)
        super().__init__(self._format_message())

    def add_parent(self, parent: Any) -> "ModifierError":
        """
        Add a parent to the beginning of the path.

        This is called as the exception bubbles up through nested Conf calls,
        building a path like: TEMPLATES[0]['OPTIONS']['context_processors']
        """
        self.path.insert(0, parent)
        # Update the exception message with the new path
        self.args = (self._format_message(),)
        return self

    def _format_message(self) -> str:
        """Format the error message with the full path to the problematic setting"""
        if not self.path:
            return self.msg

        # Build path string like: TEMPLATES[0]['OPTIONS']['context_processors']
        path_parts = []
        for i, part in enumerate(self.path):
            if i == 0:
                # First part is the root setting name
                path_parts.append(str(part))
            elif isinstance(part, int):
                # List index
                path_parts.append(f"[{part}]")
            else:
                # Dict key
                path_parts.append(f"['{part}']")

        path_str = "".join(path_parts)
        return f"{path_str}: {self.msg}"


class Modifier:
    """
    Modify an object in place
    """

    def __call__(self, obj: Any) -> Any:
        return obj


class Env:
    """
    Collect an environment variable (convenience wrapper for os.getenv)
    """

    def __init__(self, name: str, default: Any = None):
        self.name = name
        self.default = default

    def __call__(self, obj: Any) -> Any:
        return getenv(self.name, self.default)


class Append:
    """
    Append one or more values to a list

    If the target is a tuple, it will be converted to a list.
    """

    def __init__(self, *values: Any):
        self.values = values

    def __call__(self, obj: Any) -> Any:
        if isinstance(obj, tuple):
            obj = list(obj)
        if not callable(getattr(obj, "append", None)):
            raise ModifierError(f"Cannot append to a {type(obj).__name__}")
        obj.extend(self.values)
        return obj


class Remove:
    """
    Remove a value from a list, or a key from a dict
    """

    def __init__(self, value: Any):
        self.value = value

    def __call__(self, obj: Any) -> Any:
        if hasattr(obj, "remove"):
            obj.remove(self.value)
        elif isinstance(obj, dict):
            obj.pop(self.value)
        else:
            raise ModifierError(f"Cannot remove from a {type(obj).__name__}")
        return obj


def expand_dunder_path(path: str, value: Any) -> tuple[str, Any]:
    parts = path.split("__")
    root_conf = conf = Conf()
    # Skip the first part - it's the root key we return
    for i, part in enumerate(parts[1:]):
        if part.isdigit():
            part = f"_{part}"

        # If this is the last part, set the value directly
        if i == len(parts) - 2:  # -2 because we sliced off the first part
            conf.kwops[part] = value
        else:
            new_conf = Conf()
            conf.kwops[part] = new_conf
            conf = new_conf

    return parts[0], root_conf


class Conf:
    """
    Helper to modify a setting
    """

    ops: list[Modifier | Callable]
    kwops: dict[str, Modifier | Callable]

    # Modifiers
    env = Env
    append = Append
    remove = Remove

    def __init__(
        self, *ops: Conf | Modifier | Callable, **kwops: Conf | Modifier | Callable
    ):
        self.ops = list(ops)
        self.kwops = kwops

    def __call__(self, setting: Any) -> Any:
        for op in self.ops:
            setting = op(setting)

        for attr, op in self.kwops.items():
            # Expand attr dunder paths
            if "__" in attr:
                attr, op = expand_dunder_path(attr, op)

            if callable(op):
                # We have a callable, Conf or Modifier
                if attr.startswith("_") and attr[1:].isdigit():
                    # It's a list index in format _N - expecting a list
                    try:
                        attr_int = int(attr[1:])
                    except Exception as e:
                        raise ModifierError("not a list index", attr)

                    if not isinstance(setting, list):
                        raise ModifierError("not a list", attr_int)

                    val = setting[attr_int]

                    try:
                        setting[attr_int] = op(val)
                    except ModifierError as e:
                        e.add_parent(attr_int)
                        raise

                else:
                    # Top level will be Django settings object
                    # Check if we can use getattr/setattr (settings-like object)
                    if hasattr(setting, "__getattr__") and hasattr(
                        setting, "__setattr__"
                    ):
                        val = getattr(setting, attr, None)

                        # If setting doesn't exist and op is a plain callable (not Modifier/Conf),
                        # set it as-is (backward compatibility for callables like WHITENOISE_ADD_HEADERS_FUNCTION)
                        if val is None and not isinstance(op, (Modifier, Conf)):
                            setattr(setting, attr, op)
                            continue

                        try:
                            setattr(setting, attr, op(val))
                        except ModifierError as e:
                            e.add_parent(attr)
                            raise
                        continue

                    # Otherwise expecting a dict
                    if not isinstance(setting, dict):
                        raise ModifierError("not a dict", attr)
                    val = setting.get(attr)

                    # If dict key doesn't exist and op is a plain callable (not Modifier/Conf),
                    # set it as-is
                    if val is None and not isinstance(op, (Modifier, Conf)):
                        setting[attr] = op
                        continue

                    try:
                        setting[attr] = op(val)
                    except ModifierError as e:
                        e.add_parent(attr)
                        raise

            else:
                # Not callable, op is a value
                if hasattr(setting, "__getattr__") and hasattr(setting, "__setattr__"):
                    setattr(setting, attr, op)

                elif isinstance(setting, (dict, list)):
                    setting[attr] = op

                else:
                    raise ModifierError("not a dict or list", attr)

        return setting
