import math
from dataclasses import dataclass
from functools import cache, cached_property
from typing import Final, Iterable, NamedTuple

from formatting import get_formatting

from ..helpers import json_str
from ..types import FlatTextComponent, TextComponent


@dataclass(frozen=True)
class FormattingItem:
    key: Final[str]
    value: Final[object]

    @cached_property
    def _json(self):
        return f",{json_str(self.key)}:{json_str(self.value)}"

    @cached_property
    def cost(self):
        return len(self._json)

    def __hash__(self):
        return hash(self._json)


def get_formatting_items(component: TextComponent):
    return frozenset(
        FormattingItem(key, value) for key, value in get_formatting(component).items()
    )


def get_cost(formatting_items: Iterable[FormattingItem]):
    return sum(item.cost for item in formatting_items)


# A list for which the first element is the parent formatting, and each ellipsis is a
#  placeholder for a subcomponent inheriting from the formatting.
FactoredFormattingList = list[
    frozenset[FormattingItem] | ellipsis | "FactoredFormattingList"
]


class FactoredFormattings(NamedTuple):
    value: FactoredFormattingList
    cost: int


def factor_common_formatting(subcomponents: list[FlatTextComponent]):
    """Wraps certain ranges of subcomponents into arrays, utilizing array inheritance to
    reduce redundant formatting in the wrapped subcomponents.

    ⚠️ Only for use in `minify`. May mutate the inputted subcomponents.

    >>> minify(
    >>>     [
    >>>         {"text": "a", "color": "red"},
    >>>         {"text": "b", "color": "green"},
    >>>         {"text": "c", "color": "blue"},
    >>>         {"text": "d", "color": "green"},
    >>>     ]
    >>> )
    [
        {"text": "a", "color": "red"},
        [{"text": "b", "color": "green"}, {"text": "c", "color": "blue"}, "d"],
    ]
    """

    @cache
    def factor_and_get_cost(
        formattings: tuple[frozenset[FormattingItem], ...],
        parent_formatting: frozenset[FormattingItem],
    ) -> FactoredFormattings:
        """Factors a subtuple of the inputted `formattings` and gets its cost."""

        if not formattings:
            return FactoredFormattings([], cost=0)

        if len(formattings) == 1:
            formatting = formattings[0]

            # TODO: Change every instance of this condition to be whether the
            #  `parent_formatting` fully covers this `formatting` (based on whether its
            #  content is whitespace or line breaks (precompute this)) rather than
            #  whether they equal.
            if formatting == parent_formatting:
                return FactoredFormattings([...], cost=0)
            else:
                # If this node doesn't accept the parent formatting, then wrap it in the
                #  formatting it does accept.
                return FactoredFormattings(
                    [[formatting, ...]],
                    cost=get_cost(formatting),
                )

        factored_list: FactoredFormattingList = []

        # The index in `formattings` at which the next subtuple needs to start.
        subtuple_start = 0
        for formatting in formattings:
            if formatting == parent_formatting:
                # Skip this formatting since it's already covered by the parent.
                subtuple_start += 1
                factored_list.append(...)
            else:
                # This formatting isn't covered by the parent, so this is where the next
                #  subtuple needs to start in order for everything to be covered.
                break

        # The formatting at the start of the subtuple.
        first_subtuple_formatting = formattings[subtuple_start]

        # The default best cost is infinity instead of `None` so it isn't necessary to
        #  handle `None` as a special case, and anything is cheaper than infinity.
        best_cost = math.inf
        # The factoring of the subtuple that results in the best cost.
        best_subtuple_factoring: FactoredFormattings | None = None
        # The factoring of the formattings after the subtuple that results in the best
        #  cost.
        best_remainder_factoring: FactoredFormattings | None = None

        for subtuple_end in range(subtuple_start + 1, len(formattings)):
            subtuple = formattings[subtuple_start:subtuple_end]

            remainder_factoring = factor_and_get_cost(
                formattings[subtuple_end:], parent_formatting
            )
            if remainder_factoring.cost >= best_cost:
                continue

            # The set of potential formattings to apply to the subtuple.
            # TODO: Use https://discord.com/channels/343250948233101312/447171940260773888/1003116360487931935 for this.
            potential_formattings = {first_subtuple_formatting}

            for potential_formatting in potential_formattings:
                # TODO: Ensure this set difference does what I think it does.
                child_formatting = potential_formatting - parent_formatting

                cost = get_cost(child_formatting) + remainder_factoring.cost
                if cost >= best_cost:
                    continue

                subtuple_factoring = factor_and_get_cost(subtuple, potential_formatting)
                cost += subtuple_factoring.cost
                if cost >= best_cost:
                    continue

                best_cost = cost
                best_subtuple_factoring = subtuple_factoring
                best_remainder_factoring = remainder_factoring
