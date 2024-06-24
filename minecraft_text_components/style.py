from typing import Unpack

from .minify import minify
from .types import TextComponent, TextComponentFormatting


def style(
    component: TextComponent,
    **formatting: Unpack[TextComponentFormatting],
):
    """Makes the specified text component inherit the specified formatting,
    automatically minified.
    """

    return minify({"text": "", **formatting, "extra": [component]})
