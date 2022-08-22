from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Any, ClassVar, Final


@dataclass
class container(AbstractContextManager["container"]):
    """A context manager for the maximum advance of a line of text in in-game pixels.
    Defaults to `container.chat`.

    To set the container width for the duration of a `with` block:

    >>> with container.book:
    >>>     ...

    >>> with container(123):
    >>>     ...

    To set the container width persistently:

    >>> container.width = container.book.width
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

    _past_widths: Final = field(default_factory=list[float], init=False, repr=False)

    def __enter__(self):
        self._past_widths.append(container.width)
        container.width = self.width
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        container.width = self._past_widths.pop()


container.chat = container(320)
container.book = container(114)
container.sign = container(90)

# Set the default container to chat.
container.width = container.chat.width
