from advances.get_line_advance import get_line_advance

from ..split import split
from ..types import TextComponent


def get_advance(component: TextComponent):
    return max(get_line_advance(line) for line in split(component, "\n"))
