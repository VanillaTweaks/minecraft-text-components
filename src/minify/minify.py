from ..flat import flat
from ..types import TextComponent
from .factor_common_formatting import factor_common_formatting
from .merged import merged
from .reduce import reduced


def minify(component: TextComponent) -> TextComponent:
    """Transforms a text component to be as short and simplified as possible without
    changing its in-game appearance.
    """

    output = flat(component)
    output = reduced(output)
    output = merged(output)

    output = list(output)

    if len(output) == 1:
        return output[0]

    if len(output) == 0:
        return ""

    return factor_common_formatting(output)
