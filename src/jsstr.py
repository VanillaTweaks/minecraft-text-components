from .types import TextComponentText


def jsstr(component: TextComponentText) -> str:
    """Converts a `TextComponentText` to a `str` similarly to how it would be converted
    to a string in JavaScript.

    >>> jsstr("hello")
    "hello"
    >>> jsstr(42)
    "42"
    >>> jsstr(True)
    "true"
    """

    if isinstance(component, bool):
        return str(component).lower()

    return str(component)
