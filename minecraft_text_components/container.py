import re
from abc import ABCMeta
from contextlib import AbstractContextManager
from typing import Any, ClassVar, Final, cast


class ContainerMetaclass(ABCMeta):
    def __getattr__(self, name: str):
        if name == "width":
            raise AttributeError(
                "The current container has no width. To learn how to set the width, "
                "see the docstring of `minecraft_text_components.container`:\n\n    "
                + re.sub(r"\n {4}$", "", cast(str, container.__doc__))
            )


class container(AbstractContextManager["container"], metaclass=ContainerMetaclass):
    """A context manager for the maximum advance of a line of text in in-game pixels.

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
    none: ClassVar["container"]
    # A container with the width of chat with default settings.
    chat: ClassVar["container"]
    # A container with the width of a written book.
    book: ClassVar["container"]
    # A container with the width of a sign.
    sign: ClassVar["container"]

    width: float

    _past_widths: Final[list[float | None]]

    def __init__(self, width: float | None):
        if width is not None:
            self.width = width

        self._past_widths = []

    def __enter__(self):
        self._past_widths.append(getattr(container, "width", None))
        if hasattr(self, "width"):
            container.width = self.width

        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        previous_width = self._past_widths.pop()
        if previous_width is None:
            del container.width
        else:
            container.width = previous_width

    def __repr__(self):
        return f"container(width={getattr(self, 'width', None)})"


container.none = container(None)
container.chat = container(320)
container.book = container(114)
container.sign = container(90)
