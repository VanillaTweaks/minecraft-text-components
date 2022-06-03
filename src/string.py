from .types import TextComponentText


def string(text: TextComponentText):
    """Converts a `TextComponentText` to a `str` similarly to how it would be converted
    to a string in JavaScript.

    >>> string("hello")
    "hello"
    >>> string(42)
    "42"
    >>> string(True)
    "true"
    """

    if isinstance(text, bool):
        return str(text).lower()

    return str(text)
