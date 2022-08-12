from ..flat import flat
from ..types import TextComponent
from .disable_inheritance_if_necessary import disable_inheritance_if_necessary
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

    unfactored_output = list(output)

    if len(unfactored_output) == 1:
        return unfactored_output[0]

    if len(unfactored_output) == 0:
        return ""

    factored_output = factor_common_formatting(unfactored_output)

    if not isinstance(factored_output, list):
        return factored_output

    output = disable_inheritance_if_necessary(factored_output)

    return output
