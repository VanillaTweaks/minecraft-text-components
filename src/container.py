from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Any, ClassVar, Final


@dataclass
class container(AbstractContextManager["container"]):
    """A context manager for the maximum advance of a line of text in in-game pixels.
    Defaults to `container.chat` when not in any context.
    """

    # A container with the width of chat with default settings.
    chat: ClassVar["container"]
    # A container with the width of a written book.
    book: ClassVar["container"]

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

# Set the default container to chat.
container.width = container.chat.width
