from ..split import split
from ..types import TextComponent
from .get_line_advance import get_line_advance


def get_advance(component: TextComponent):
    """Gets the width in in-game pixels that a text component takes up."""

    return max(get_line_advance(line) for line in split(component, "\n"))
