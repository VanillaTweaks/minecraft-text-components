import itertools
import math
from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache, cached_property
from types import EllipsisType
from typing import Any, Final, NamedTuple, cast

from ..formatting import FORMATTING_KEYS, get_formatting, is_affected_by_inheriting
from ..helpers import json_str
from ..prevent_inheritance import prevent_inheritance
from ..types import (
    FlatTextComponent,
    TextComponent,
    TextComponentDict,
    TextComponentFormatting,
)
from .merged import merged
from .reduce import reduced


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


FormattingSet = frozenset[FormattingItem]

# A list for which the first element is the parent formatting (if there is any), and
#  each ellipsis is a placeholder for a subcomponent inheriting from the formatting.
FactoredFormattingList = list["FormattingSet | EllipsisType | FactoredFormattingList"]


class FactoredFormattings(NamedTuple):
    value: FactoredFormattingList
    cost: float


def get_formatting_set(formatting: TextComponentFormatting):
    """Converts a `TextComponentFormatting` to a `FormattingSet`."""

    return FormattingSet(
        FormattingItem(key, value) for key, value in formatting.items()
    )


def get_component_formatting(items: Iterable[FormattingItem]):
    """Converts `FormattingItem`s to `TextComponentFormatting`."""

    return cast(TextComponentFormatting, {item.key: item.value for item in items})


def get_cost(formatting_items: Iterable[FormattingItem]):
    return sum(item.cost for item in formatting_items)


def set_component_formatting(
    component: FlatTextComponent, formatting: TextComponentFormatting
):
    """Returns a `TextComponentDict` with the content of `component` and the formatting of
    `formatting`.
    """

    if isinstance(component, dict):
        content = {
            key: value for key, value in component.items() if key not in FORMATTING_KEYS
        }
    else:
        content = {"text": component}

    return cast(TextComponentDict, content | formatting)


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

    formattings: Final = [
        get_formatting_set(get_formatting(subcomponent))
        for subcomponent in subcomponents
    ]

    @cache
    def parent_covers_subcomponent(
        parent: FormattingSet,
        # The index of the subcomponent to check.
        i: int,
    ):
        """Checks whether the parent formatting can substitute the subcomponent's
        formatting without affecting the subcomponent.
        """

        formatting = formattings[i]

        return parent == formatting or (
            parent > formatting
            and not is_affected_by_inheriting(
                subcomponents[i],
                {formatting_item.key for formatting_item in parent},
            )
        )

    @cache
    def factor_and_get_cost(
        *,
        parent: FormattingSet,
        # The index to start the range of `subcomponents` to factor.
        start: int,
        # The index to end the range of `subcomponents` to factor.
        end: int,
    ) -> FactoredFormattings:
        """Factors a range of the inputted `formattings` and gets its cost."""

        # The formattings which only inherit from the parent and precede the next
        #  sublist.
        formattings_covered_by_parent: FactoredFormattingList = []

        # The index in `subcomponents` at which the next sublist needs to start.
        sublist_start = start
        for i in range(start, end):
            if parent_covers_subcomponent(parent, i):
                # Skip this subcomponent since it's already covered by the parent.
                sublist_start += 1
                formattings_covered_by_parent.append(...)
            else:
                # This formatting isn't covered by the parent, so this is where the next
                #  sublist needs to start in order for everything to be covered.
                break

        if sublist_start == end:
            # All the formattings are the same as the parent, so no factoring needs to
            #  be done.
            return FactoredFormattings(value=formattings_covered_by_parent, cost=0)

        best_cost = math.inf
        best_sublist_formatting: FormattingSet | None = None
        best_sublist_factoring: FactoredFormattings | None = None
        best_remainder_factoring: FactoredFormattings | None = None

        # The formattings to consider applying to the sublist.
        potential_formattings: set[FormattingSet] | None = None
        # A mapping from each formatting key to the set of formatting items which are in
        #  `potential_formattings` with that key.
        potential_formatting_items: dict[str, set[FormattingItem]] = {}
        # Components that might conflict with the `potential_formattings` and haven't
        #  been checked by `update_potential_formattings` yet.
        potentially_conflicting_components: list[FlatTextComponent] = []

        parent_keys = {item.key for item in parent}

        def compute_potential_formattings():
            nonlocal potential_formattings

            potential_formattings = set()

            first_sublist_formatting = formattings[sublist_start]
            parent_component_formatting = get_component_formatting(parent)

            # A power set of the items in the first sublist element, excluding the empty
            #  set.
            combinations = itertools.chain.from_iterable(
                # Exclude formatting items already in the parent, since making a new
                #  sublist for an item the parent already has would be pointless.
                itertools.combinations(first_sublist_formatting - parent, length)
                for length in range(1, len(first_sublist_formatting) + 1)
            )

            for combination in combinations:
                for item in combination:
                    if item.key in potential_formatting_items:
                        potential_formatting_items[item.key].add(item)
                    else:
                        potential_formatting_items[item.key] = {item}

                potential_formattings.add(
                    get_formatting_set(
                        # Every potential formatting should inherit from the parent.
                        parent_component_formatting
                        | get_component_formatting(combination)
                    )
                )

            # Note: `potential_formattings` can't be empty at this point, because
            #  `first_sublist_formatting - parent` (what generates the `combinations`)
            #  can't be empty either. If it were, then `first_sublist_formatting` would
            #  be in the `formattings_covered_by_parent`, not in the sublist.

        def remove_conflicting_potential_formattings():
            """Removes any `potential_formattings` and `potential_formatting_items` that
            conflict with the new components in `potential_conflicting_components`, then
            clears the `potential_conflicting_components`.
            """

            nonlocal potential_formattings

            keys_to_remove = {
                formatting_key
                for formatting_key in potential_formatting_items.keys()
                # A parent formatting key can never conflict with a component in the
                #  sublist, so we can check that first as a shortcut.
                if formatting_key not in parent_keys
                and any(
                    is_affected_by_inheriting(component, {formatting_key})
                    for component in potentially_conflicting_components
                )
            }

            if keys_to_remove:
                items_to_remove: set[FormattingItem] = set()
                for key_to_remove in keys_to_remove:
                    items_to_remove |= potential_formatting_items.pop(key_to_remove)

                assert potential_formattings is not None
                potential_formattings = {
                    formatting
                    for formatting in potential_formattings
                    if not formatting & items_to_remove
                }

            potentially_conflicting_components.clear()

        def update_potential_formattings():
            """Updates the `potential_formattings` and clears the
            `potentially_conflicting_components`.
            """

            if potential_formattings is None:
                compute_potential_formattings()

            remove_conflicting_potential_formattings()

        for sublist_end in range(sublist_start + 1, end + 1):
            sublist_length = sublist_end - sublist_start
            sublist_components = subcomponents[sublist_start:sublist_end]

            # Add each sublist component to the `potentially_conflicting_components`,
            #  excluding the first since the potential formattings are taken from the
            #  first component and thus cannot conflict with it.
            if sublist_length != 1:
                potentially_conflicting_components.append(sublist_components[-1])

            remainder_factoring = factor_and_get_cost(
                parent=parent, start=sublist_end, end=end
            )
            if remainder_factoring.cost >= best_cost:
                continue

            if sublist_length == 1:
                # If the sublist only has one element, it's unnecessary to update and
                #  try all the `potential_formattings`.
                formattings_to_try = {formattings[sublist_start]}
            else:
                update_potential_formattings()
                formattings_to_try = cast(set[FormattingSet], potential_formattings)

            for formatting in formattings_to_try:
                sublist_formatting = formatting - parent

                cost = get_cost(sublist_formatting) + remainder_factoring.cost
                if cost >= best_cost:
                    continue

                sublist_factoring = factor_and_get_cost(
                    parent=formatting, start=sublist_start, end=sublist_end
                )

                cost += sublist_factoring.cost
                if len(sublist_factoring.value) > 1:
                    # Add 2 for the cost of the square brackets when the sublist can't
                    #  be reduced to just one element.
                    cost += 2

                if cost >= best_cost:
                    continue

                best_cost = cost
                best_sublist_formatting = sublist_formatting
                best_sublist_factoring = sublist_factoring
                best_remainder_factoring = remainder_factoring

        # The above loops must have ran for at least one iteration.
        assert best_sublist_formatting is not None
        assert best_sublist_factoring is not None
        assert best_remainder_factoring is not None

        return FactoredFormattings(
            value=[
                *formattings_covered_by_parent,
                [best_sublist_formatting, *best_sublist_factoring.value],
                *best_remainder_factoring.value,
            ],
            cost=best_cost,
        )

    subcomponent_iterator = iter(subcomponents)

    def get_factored_component(
        factoring: FactoredFormattingList,
    ) -> TextComponent:
        """Converts a `FactoredFormattingList` to a `TextComponent`."""

        formatting: TextComponentFormatting = {}
        if isinstance(factoring[0], frozenset):
            formatting = get_component_formatting(cast(FormattingSet, factoring.pop(0)))

        contents = cast(list[EllipsisType | FactoredFormattingList], factoring)
        output: list[TextComponent] = []

        flat_subcomponents: list[FlatTextComponent] = []

        def append_flat_subcomponent(subcomponent: FlatTextComponent):
            if isinstance(subcomponent, dict):
                subcomponent = cast(
                    TextComponentDict,
                    {
                        key: value
                        for key, value in subcomponent.items()
                        # Remove the items that will be inherited from the `formatting`.
                        if formatting.get(key) != value
                    },
                )

            flat_subcomponents.append(subcomponent)

        def end_flat_subcomponents():
            if not flat_subcomponents:
                return

            output.extend(merged(reduced(flat_subcomponents)))

            flat_subcomponents.clear()

        for item in contents:
            if item is ...:
                append_flat_subcomponent(next(subcomponent_iterator))
                continue

            subcomponent = get_factored_component(cast(FactoredFormattingList, item))

            if isinstance(subcomponent, list):
                end_flat_subcomponents()

                output.append(subcomponent)
                continue

            append_flat_subcomponent(subcomponent)

        end_flat_subcomponents()

        if formatting:
            # Check if the output list's first item shouldn't take `formatting`'s items.
            if (
                (
                    # If taking the `formatting`'s items would affect the component, the
                    #  component shouldn't take them.
                    isinstance(output[0], dict)
                    and is_affected_by_inheriting(
                        cast(
                            TextComponentDict,
                            {
                                key: value
                                for key, value in output[0].items()
                                # Let the `formatting` overwrite any items.
                                if key not in formatting
                            },
                        ),
                        # Exclude the `formatting` keys `output[0]` doesn't have, since
                        #  those ones are specifically intended to affect the component.
                        formatting.keys() & output[0].items(),
                    )
                )
                # The algorithm would've put the `formatting` on that list to begin with
                #  if it were optimal.
                or isinstance(output[0], list)
            ):
                # The formatting must be inserted as a new first element instead of
                #  being applied to the existing one.

                # It's not necessary to call `prevent_inheritance` here because the
                #  original first element won't be inherited anyway, since we're about
                #  to insert a new first element that should be inherited instead.

                output.insert(0, cast(TextComponentDict, {"text": ""} | formatting))

            else:
                # If the first element has formatting the other elements would inherit
                #  but shouldn't, then we should let `prevent_inheritance` insert an
                #  empty string to take the `formatting` instead of the first element.
                output = prevent_inheritance(output)

                if isinstance(output[0], dict):
                    output[0] |= cast(Any, formatting)
                else:
                    output[0] = cast(
                        TextComponentDict, {"text": output[0]} | formatting
                    )

        else:
            output = prevent_inheritance(output)

        if len(output) == 1:
            return output[0]

        return output

    return get_factored_component(
        factor_and_get_cost(
            parent=FormattingSet(),
            start=0,
            end=len(subcomponents),
        ).value
    )
