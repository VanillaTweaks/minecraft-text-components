from typing_extensions import Unpack

from .minify import minify
from .types import TextComponent, TextComponentFormatting


def style(
    component: TextComponent,
    **formatting: Unpack[TextComponentFormatting],
):
    """Makes the specified text component inherit the specified formatting,
    automatically minified.
    """

    if formatting is None:
        formatting = {}

    return minify({"text": "", **formatting, "extra": [component]})  # type: ignore
