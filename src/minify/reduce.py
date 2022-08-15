from collections.abc import Iterable

from ..formatting import WHITESPACE_UNAFFECTED_BY_KEYS
from ..helpers import js_str
from ..regex import LINE_BREAKS
from ..types import FlatTextComponent


def reduce(component: FlatTextComponent):
    """Reduces the size of the inputted component using only the information within it.

    ⚠️ Only for use in `minify`. May mutate the inputted component.
    """

    from .minify import minify

    if isinstance(component, dict):
        if "text" in component:
            if component["text"] == "":
                return ""

            text = js_str(component["text"])
            text_is_whitespace = text.isspace()

            if text_is_whitespace:
                for key in WHITESPACE_UNAFFECTED_BY_KEYS:
                    if key in component:
                        del component[key]

            # Check if the component's formatting has no effect on its `text`.
            if (
                # Check if there is only `text`, no formatting.
                len(component) == 1
                # Check if the text is only line breaks, so formatting does nothing.
                or (text_is_whitespace and LINE_BREAKS.match(text))
            ):
                # Reduce this component to a plain string.
                return text

        elif "with" in component:
            # Recursively minify `with` values.
            component["with"] = [minify(value) for value in component["with"]]

    return component


def reduced(subcomponents: Iterable[FlatTextComponent]):
    """Reduces the size of each inputted subcomponent using only the information within
    it.

    ⚠️ Only for use in `minify`. May mutate the inputted subcomponents.
    """

    for subcomponent in subcomponents:
        reduced_subcomponent = reduce(subcomponent)

        if reduced_subcomponent == "":
            # Reduce empty strings to nothing by not yielding anything.
            continue

        yield reduced_subcomponent
