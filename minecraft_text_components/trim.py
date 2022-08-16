import re

from .join import join
from .split import split
from .types import TextComponent

NON_WHITESPACE_PATTERN = re.compile(r"(\S+)")


def trim(component: TextComponent):
    return join(list(split(component, NON_WHITESPACE_PATTERN))[1:-1], "")
