import re
from abc import ABCMeta
from contextlib import AbstractContextManager
from typing import Any, ClassVar, Final, cast


class ContainerMetaclass(ABCMeta):
    def __getattr__(self, name: str):
        if name == "width":
            raise AttributeError(
                "The container width is unset. For information on how to set it, see "
                "the docstring of `minecraft_text_components.container`:\n\n    "
                + re.sub(r"\n {4}$", "", cast(str, container.__doc__))
            )


class container(AbstractContextManager["container"], metaclass=ContainerMetaclass):
    """A context manager for the maximum advance of a line of text in in-game pixels.

    To set the container width for the duration of a `with` block:

    >>> with container.chat:
    >>>     ...

    >>> with container(123):
    >>>     ...

    To set the container width persistently:

    >>> container.width = container.chat.width
    >>> ...

    >>> container.width = 123
    >>> ...
    """

    # A container with the width of chat with default settings.
    chat: ClassVar["container"]
    # A container with the width of a written book.
    book: ClassVar["container"]
    # A container with the width of a sign.
    sign: ClassVar["container"]

    width: float

    _past_widths: Final[list[float]]

    def __init__(self, width: float):
        self.width = width
        self._past_widths = []

    def __enter__(self):
        self._past_widths.append(container.width)
        container.width = self.width
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        container.width = self._past_widths.pop()

    def __repr__(self):
        return f"container(width={self.width})"


container.chat = container(320)
container.book = container(114)
container.sign = container(90)
