import math

from .advances import get_char_advance
from .types import TextComponent

SPACE_ADVANCE = int(get_char_advance(" "))


def whitespace(
    advance: float,
    # Whether to floor the inputted width to the nearest valid whitespace, rather than
    #  (roughly) round which is the default.
    floor: bool = False,
) -> TextComponent:
    """Returns a text component of a combination of plain and bold spaces to achieve a
    specified width in in-game pixels.
    """

    # If the advance is small, then round up to the smallest valid advance, since the
    #  advance is most likely intended to be non-zero (unless `floor`).
    if advance > 0 and advance < SPACE_ADVANCE:
        advance = 0 if floor else SPACE_ADVANCE

    advance = math.floor(advance)

    if advance == 0:
        return ""
    if advance == 6:
        advance = 5
    elif advance == 7:
        advance = 5 if floor else 8
    elif advance == 11:
        advance = 10
    elif advance < 0:
        raise ValueError("The `whitespace` advance must not be negative")

    plain_spaces, bold_spaces = divmod(advance, SPACE_ADVANCE)

    component: TextComponent = []

    if plain_spaces:
        component.append(" " * plain_spaces)
    if bold_spaces:
        component.append({"text": " " * bold_spaces, "bold": True})

    if not component:
        return ""

    if len(component) == 1:
        return component[0]

    return component
