from ..flat import flat
from ..types import TextComponent, TextComponentFormatting
from .get_char_advance import get_char_advance


def get_line_advance(
    component: TextComponent,
    formatting: TextComponentFormatting = {},
) -> float:
    """Gets the width in in-game pixels that a single-line `TextComponent` takes up."""

    advance = 0

    if not isinstance(component, (dict, list)):
        for char in str(component):
            advance += get_char_advance(char, formatting)

        return advance

    for subcomponent in flat(component):
        if isinstance(subcomponent, dict):
            if "text" not in subcomponent:
                raise ValueError(
                    "It is impossible to determine the advance of the following text "
                    f"component:\n{repr(subcomponent)}"
                )

            advance += get_line_advance(subcomponent["text"])  # type: ignore
            continue

        advance += get_line_advance(subcomponent)

    return advance
