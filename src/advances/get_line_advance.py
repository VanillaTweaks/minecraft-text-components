from ..flat import flat
from ..helpers import js_str
from ..types import TextComponent, TextComponentFormatting, TextComponentText
from .get_char_advance import get_char_advance


def get_line_advance(
    component: TextComponent,
    formatting: TextComponentFormatting | None = None,
) -> float:
    """Gets the width in in-game pixels that a single-line text component takes up."""

    if formatting is None:
        formatting = {}

    advance = 0

    if isinstance(component, TextComponentText):
        for char in js_str(component):
            advance += get_char_advance(char, formatting)

        return advance

    for subcomponent in flat(component):
        if isinstance(subcomponent, dict):
            if "text" not in subcomponent:
                raise ValueError(
                    "It is impossible to determine the advance of the following text "
                    f"component:\n{repr(subcomponent)}"
                )

            advance += get_line_advance(subcomponent["text"], formatting)
            continue

        advance += get_line_advance(subcomponent, formatting)

    return advance
