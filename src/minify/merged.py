from collections.abc import Iterator

from ..formatting import FORMATTING_KEYS, WHITESPACE_AFFECTED_BY_KEYS
from ..types import FlatTextComponent


def merged(subcomponents: Iterator[FlatTextComponent]):
    """Merges adjacent elements of the inputted subcomponents wherever possible.

    ⚠️ Only for use in `minify`. May mutate the inputted subcomponents.
    """

    try:
        previous_subcomponent = next(subcomponents)

    except StopIteration:
        return

    for subcomponent in subcomponents:
        # Try to merge this subcomponent with the previous one.

        # Whether this subcomponent was successfully merged with the previous one.
        merged = False

        if isinstance(subcomponent, dict):
            if "text" in subcomponent:
                # The subcomponent has `text` with distinguishable formatting.
                #
                # (We know the formatting is distinguishable because the previous step
                #  of the `minify` algorithm is `reduce`, which removes
                #  indistinguishable formatting.)

                if isinstance(previous_subcomponent, dict):
                    if "text" in previous_subcomponent:
                        # Both this subcomponent and the previous one have `text` with
                        #  distinguishable formatting.

                        text = str(subcomponent["text"])
                        text_is_whitespace = text.isspace()
                        previous_text = str(previous_subcomponent["text"])
                        previous_text_is_whitespace = previous_text.isspace()

                        keys_which_must_equal = FORMATTING_KEYS
                        if text_is_whitespace or previous_text_is_whitespace:
                            keys_which_must_equal = WHITESPACE_AFFECTED_BY_KEYS

                        if all(
                            subcomponent.get(key) == previous_subcomponent.get(key)
                            for key in keys_which_must_equal
                        ):
                            # Merge their `text`s.

                            if not text_is_whitespace:
                                # The previous subcomponent might be whitespace, so
                                #  merging this subcomponent into it might cause some of
                                #  this subcomponent's formatting to be lost. Instead,
                                #  because this subcomponent isn't whitespace, merge the
                                #  previous subcomponent into this one.
                                previous_subcomponent = subcomponent

                            previous_subcomponent["text"] = previous_text + text
                            merged = True

                elif
