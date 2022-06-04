from ..flat import flat
from ..formatting import get_formatting_keys, is_affected_by_inheriting
from ..types import TextComponent


def disable_inheritance_if_necessary(subcomponents: list[TextComponent]):
    """Returns the inputted list, but inserts `""` at the start if necessary to prevent
    other subcomponents from inheriting properties from the first.

    ⚠️ Only for use in `minify`. Assumes `len(subcomponents) > 1`.
    """

    formatting_keys = get_formatting_keys(subcomponents[0])

    if formatting_keys:
        for subcomponent in subcomponents[1:]:

            for flat_subcomponent in flat(subcomponent):
                if is_affected_by_inheriting(flat_subcomponent, formatting_keys):
                    return ["", *subcomponents]

    return subcomponents
