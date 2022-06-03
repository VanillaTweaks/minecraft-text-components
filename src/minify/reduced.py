from collections.abc import Iterator

from ..formatting import WHITESPACE_UNAFFECTED_BY_KEYS
from ..regex import LINE_BREAKS
from ..types import FlatTextComponent
from .minify import minify


def reduced(subcomponents: Iterator[FlatTextComponent]):
    """Reduces the size of each inputted subcomponent using only the information within
    it.

    ⚠️ Only for use in `minify`. May mutate the inputted subcomponents.
    """

    for subcomponent in subcomponents:
        if isinstance(subcomponent, dict):
            if "text" in subcomponent:
                if subcomponent["text"] == "":
                    # Reduce empty strings to nothing by not yielding anything.
                    continue

                text = str(subcomponent["text"])
                text_is_whitespace = text.isspace()

                if text_is_whitespace:
                    for key in WHITESPACE_UNAFFECTED_BY_KEYS:
                        del subcomponent[key]

                # Check if the subcomponent's formatting has no effect on its `text`.
                if (
                    # Check if there is only `text`, no formatting.
                    len(subcomponent) == 1
                    # Check if the text is only line breaks, so formatting does nothing.
                    or (text_is_whitespace and LINE_BREAKS.match(text))
                ):
                    # Reduce this subcomponent to a plain string.
                    yield text
                    continue

            elif "with" in subcomponent:
                # Recursively minify `with` values.
                subcomponent["with"] = [minify(value) for value in subcomponent["with"]]

        # We don't have to avoid yielding `""` here because `flat`, the step of the
        #  `minify` algorithm before this one, never yields `""`.

        yield subcomponent
