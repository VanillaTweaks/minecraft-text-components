from .types import TextComponentText


def js_str(component: TextComponentText) -> str:
    """Converts a `TextComponentText` to a `str` similarly to how it would be converted
    to a string in JavaScript.

    >>> js_str("hello")
    "hello"
    >>> js_str(42)
    "42"
    >>> js_str(True)
    "true"
    """

    if isinstance(component, bool):
        return str(component).lower()

    return str(component)
