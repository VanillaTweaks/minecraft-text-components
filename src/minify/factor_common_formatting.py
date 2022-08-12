from dataclasses import dataclass
from functools import cache, cached_property
from typing import Final, Iterable, NamedTuple

from ..formatting import get_formatting, is_affected_by_inheriting
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

        # The formattings which only inherit from the parent and precede the next
        #  subtuple.
        parent_formattings: FactoredFormattingList = []

        # The index in `formattings` at which the next subtuple needs to start.
        subtuple_start = 0
        for formatting in formattings:
            # TODO: Change every instance of this condition to be whether the
            #  `parent_formatting` fully covers this `formatting` (based on whether its
            #  content is whitespace or line breaks (precompute this)) rather than
            #  whether they equal.
            if formatting == parent_formatting:
                # Skip this formatting since it's already covered by the parent.
                subtuple_start += 1
                parent_formattings.append(...)
            else:
                # This formatting isn't covered by the parent, so this is where the next
                #  subtuple needs to start in order for everything to be covered.
                break

        if subtuple_start == len(formattings):
            # All the formattings are the same as the parent, so no factoring needs to
            #  be done.
            return FactoredFormattings(parent_formattings, cost=0)

        best_cost = None
        # The factoring of the subtuple that results in the best cost.
        best_subtuple_factoring: FactoredFormattings | None = None
        # The factoring of the formattings after the subtuple that results in the best
        #  cost.
        best_remainder_factoring: FactoredFormattings | None = None

        # The formatting at the start of the subtuple.
        first_subtuple_formatting = formattings[subtuple_start]

        def is_cheaper(cost: int):
            return best_cost is None or cost < best_cost

        for subtuple_end in range(subtuple_start + 1, len(formattings)):
            subtuple = formattings[subtuple_start:subtuple_end]

            remainder_factoring = factor_and_get_cost(
                formattings[subtuple_end:], parent_formatting
            )
            if not is_cheaper(remainder_factoring.cost):
                continue

            # The set of potential formattings to apply to the subtuple.
            # TODO: all of the properties of the first node + any subset of the properties found in other nodes in the subtuple (that dont overwrite the properties of the first node, except when they have no effect on the first node)
            potential_formattings = {first_subtuple_formatting}

            # TODO: Consider caching the below process.

            potential_formatting_items = set[FormattingItem]()
            for subtuple_formatting in subtuple:
                if subtuple_formatting is first_subtuple_formatting:
                    continue

                for formatting_item in subtuple_formatting:
                    if is_affected_by_inheriting(
                        first_subtuple_component, {formatting_item.key}
                    ):
                        # This formatting item is inconsistent with the subtuple's first
                        #  component, so there's no reason to apply it to the subtuple.
                        #  If an optimal factoring did have a subtuple whose formatting
                        #  is inconsistent with its first component, then there would
                        #  need to be an additional inner subtuple covering that first
                        #  component anyway, in which case the outer subtuple might as
                        #  well start later instead.
                        continue

                    potential_formatting_items.add(formatting_item)

            for potential_formatting in potential_formattings:
                child_formatting = potential_formatting - parent_formatting

                cost = get_cost(child_formatting) + remainder_factoring.cost
                if not is_cheaper(cost):
                    continue

                subtuple_factoring = factor_and_get_cost(subtuple, potential_formatting)
                cost += subtuple_factoring.cost
                if not is_cheaper(cost):
                    continue

                best_cost = cost
                best_subtuple_factoring = subtuple_factoring
                best_remainder_factoring = remainder_factoring

        assert best_cost is not None
        assert best_subtuple_factoring is not None
        assert best_remainder_factoring is not None

        return FactoredFormattings(
            parent_formattings
            + best_subtuple_factoring.value
            + best_remainder_factoring.value,
            cost=best_cost,
        )
