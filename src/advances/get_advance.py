from ..split import split
from ..types import TextComponent
from .get_line_advance import get_line_advance


def get_advance(component: TextComponent):
    return max(get_line_advance(line) for line in split(component, "\n"))
