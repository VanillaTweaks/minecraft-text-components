from contextlib import AbstractContextManager
from typing import Any, ClassVar, Final


class Container(AbstractContextManager["Container"]):
    """A context manager for the maximum advance of a line of text in in-game pixels.
    Generally, you should use `container` instead. See `container` for more information.
    """

    width: Final[float | None]

    _previous_widths: list[float | None]

    def __init__(self, width: float | None):
        self.width = width

        self._previous_widths = []

    def __enter__(self):
        self._previous_widths.append(getattr(container, "width", None))

        if self.width is None:
            del container.width
        else:
            container.width = self.width

        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        previous_width = self._previous_widths.pop()

        if previous_width is None:
            del container.width
        else:
            container.width = previous_width

    def __repr__(self):
        return f"container(width={self.width})"


class container:
    """Holds the current maximum advance of a line of text in in-game pixels.

    To set the container width for the duration of a `with` block:

    >>> with container.chat:
    >>>     print(container.width)
    320

    >>> with container(123):
    >>>     print(container.width)
    123

    >>> with container.none:
    >>>     print(container.width)
    AttributeError

    To set the container width persistently:

    >>> container.width = container.chat.width
    >>> print(container.width)
    320

    >>> container.width = 123
    >>> print(container.width)
    123

    >>> del container.width
    >>> print(container.width)
    AttributeError
    """

    # A container with no defined width.
    none: ClassVar[Container] = Container(None)
    # A container with the width of chat with default settings.
    chat: ClassVar[Container] = Container(320)
    # A container with the width of a written book.
    book: ClassVar[Container] = Container(114)
    # A container with the width of a sign.
    sign: ClassVar[Container] = Container(90)

    width: ClassVar[float]

    def __new__(cls, width: float | None):
        return Container(width)
