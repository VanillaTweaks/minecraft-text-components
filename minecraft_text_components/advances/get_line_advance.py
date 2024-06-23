from ..flat import flat
from ..formatting import get_formatting
from ..helpers import js_str
from ..types import TextComponent, TextComponentFormatting, TextComponentText
from .get_char_advance import get_char_advance


def get_text_line_advance(
    text: TextComponentText,
    formatting: TextComponentFormatting | None = None,
) -> float:
    """Gets the width in in-game pixels that a single line of text takes up."""

    if formatting is None:
        formatting = {}

    advance = 0

    for char in js_str(text):
        advance += get_char_advance(char, formatting)

    return advance


def get_line_advance(component: TextComponent) -> float:
    """Gets the width in in-game pixels that a single-line text component takes up."""

    if isinstance(component, TextComponentText):
        return get_text_line_advance(component)

    advance = 0

    for subcomponent in flat(component):
        if isinstance(subcomponent, dict):
            if "text" not in subcomponent:
                raise ValueError(
                    "It's impossible to determine the advance of the following text "
                    f"component:\n{repr(subcomponent)}"
                )

            advance += get_text_line_advance(
                subcomponent["text"], get_formatting(subcomponent)
            )
            continue

        advance += get_text_line_advance(subcomponent)

    return advance
