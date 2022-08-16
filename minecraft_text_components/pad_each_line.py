from collections.abc import Callable

from .advances import get_line_advance
from .container import container
from .join import join
from .split import split
from .types import TextComponent
from .whitespace import whitespace
from .wrap import wrap

GetIdealPadding = Callable[[float], float]


def pad_each_line(
    component: TextComponent,
    ideal_padding_advance: float | GetIdealPadding,
):
    """Adds whitespace before each line of a text component (counting lines caused by
    wrapping), automatically minified.
    """

    get_ideal_padding: GetIdealPadding = (
        ideal_padding_advance
        if callable(ideal_padding_advance)
        else lambda _: ideal_padding_advance
    )

    def pad_line(line: TextComponent):
        advance = get_line_advance(line)

        if advance == 0:
            # If the line is empty, leave it empty rather than adding useless padding.
            return ""

        if advance > container.width:
            raise ValueError(
                "The width of the following line exceeds the container width:\n"
                + repr(line)
            )

        ideal_padding_advance = get_ideal_padding(advance)
        padding = whitespace(ideal_padding_advance)
        padding_advance = get_line_advance(padding)

        if advance + padding_advance > container.width:
            padding = whitespace(ideal_padding_advance, floor=True)

        return ["", padding, line]

    lines = split(wrap(component), "\n")
    return join([pad_line(line) for line in lines], "\n")
