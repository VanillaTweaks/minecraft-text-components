import math
from dataclasses import dataclass
from functools import cache, cached_property
from types import EllipsisType
from typing import Final, Iterable, NamedTuple, cast

from ..formatting import FORMATTING_KEYS, get_formatting, is_affected_by_inheriting
from ..helpers import json_str
from ..types import (
    FlatTextComponent,
    TextComponent,
    TextComponentDict,
    TextComponentFormatting,
    TextComponentTextDict,
)
from .merged import merged
from .reduce import reduce, reduced


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


def get_formatting_items(component: TextComponent):
    """Converts a `TextComponent` to a `FormattingSet`."""

    return FormattingSet(
        FormattingItem(key, value) for key, value in get_formatting(component).items()
    )


def get_component_formatting(formatting: FormattingSet):
    """Converts a `FormattingSet` to `TextComponentFormatting`."""

    return cast(TextComponentFormatting, {item.key: item.value for item in formatting})


def get_cost(formatting_items: Iterable[FormattingItem]):
    return sum(item.cost for item in formatting_items)


# A list for which the first element is the parent formatting, and each ellipsis is a
#  placeholder for a subcomponent inheriting from the formatting.
FactoredFormattingList = list["FormattingSet | EllipsisType | FactoredFormattingList"]


class FactoredFormattings(NamedTuple):
    value: FactoredFormattingList
    cost: float


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


FactoredTextComponent = FlatTextComponent | list["FactoredTextComponent"]


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
    def parent_formatting_covers(
        parent_formatting: FormattingSet,
        formatting: FormattingSet,
        subcomponent_index: int,
    ):
        """Checks whether the parent formatting can substitute the subcomponent's
        formatting without affecting the subcomponent.
        """

        return parent_formatting == formatting or (
            parent_formatting > formatting
            and not is_affected_by_inheriting(
                subcomponents[subcomponent_index],
                {formatting_item.key for formatting_item in parent_formatting},
            )
        )

    @cache
    def factor_and_get_cost(
        formattings: tuple[FormattingSet, ...],
        parent_formatting: FormattingSet,
        # The index in `subcomponents` of the first subcomponent which the `formattings`
        #  correspond to.
        subcomponent_start: int = 0,
    ) -> FactoredFormattings:
        """Factors a subtuple of the inputted `formattings` and gets its cost."""

        print(
            subcomponent_start,
            subcomponent_start + len(formattings),
            set(parent_formatting),
        )

        # The formattings which only inherit from the parent and precede the next
        #  subtuple.
        parent_formattings = FactoredFormattingList()

        # The index in `formattings` at which the next subtuple needs to start.
        subtuple_start = 0
        for i, formatting in enumerate(formattings, subcomponent_start):
            if parent_formatting_covers(parent_formatting, formatting, i):
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
            return FactoredFormattings(value=parent_formattings, cost=0)

        best_cost = math.inf
        best_subtuple_formatting: FormattingSet | None = None
        best_subtuple_factoring: FactoredFormattings | None = None
        best_remainder_factoring: FactoredFormattings | None = None

        # A dict which maps each formatting key to a set of formatting items with that
        #  key to consider applying to the subtuple.
        potential_formatting_items = dict[str, set[FormattingItem]]()
        # The set of potential formattings to apply to the subtuple. Like a power set of
        #  the values in `potential_formatting_items`, but each element contains at most
        #  one of each formatting key.
        potential_formattings = set[FormattingSet]()
        # Formattings with items to be passed to `add_potential_formatting_item`.
        formattings_with_potential_items = set[FormattingSet]()
        # The components corresponding to `formattings_with_potential_items`.
        components_with_potential_items = list[FlatTextComponent]()

        parent_formatting_items = {item.key: item for item in parent_formatting}

        def add_potential_formattings(
            formatting: set[FormattingItem],
            # The remaining formatting keys to add potential formattings for.
            keys: set[str],
        ):
            """Joins the specified `formatting` with every possible combination of the
            `potential_formatting_items` which have the specified `keys`, adding each
            joined combination to the `potential_formattings`.
            """

            if not keys:
                # The `formatting` does not need any more keys and is ready to be added
                #  to the `potential_formattings`.
                potential_formattings.add(FormattingSet(formatting))
                return

            key = keys.pop()

            formatting_without_conflict = formatting
            # If new formatting items would conflict with a parent formatting item,
            #  allow the parent item to be overwritten.
            if key in parent_formatting_items:
                formatting_without_conflict = formatting.copy()
                formatting_without_conflict.remove(parent_formatting_items[key])

            # Add every possible formatting item with key `key`.
            for formatting_item in potential_formatting_items[key]:
                add_potential_formattings(
                    {*formatting_without_conflict, formatting_item}, keys.copy()
                )

            # Add the possibility for no formatting item with key `key`.
            # There's no need to use copies for `formatting` and `keys` this time since
            #  this is the last time they'll be used in this iteration.
            add_potential_formattings(formatting, keys)

        @cache
        def add_potential_formatting_item(formatting_item: FormattingItem):
            """Adds a formatting item to the `potential_formatting_items` if applicable
            and updates the `potential_formattings` accordingly.
            """

            if formatting_item in parent_formatting:
                # The formatting item is already in the parent formatting, so making a
                #  new subtuple for the same item would be pointless.
                return

            # A parent formatting key can never conflict with a component in the
            #  subtuple, so we can check that first as a shortcut.
            if formatting_item.key not in parent_formatting_items and any(
                is_affected_by_inheriting(subcomponent, {formatting_item.key})
                for subcomponent in subtuple_components
            ):
                # The formatting item conflicts with a component in the subtuple, so
                #  applying it to the subtuple would result in incorrect formatting.
                return

            if formatting_item.key in potential_formatting_items:
                potential_formatting_items[formatting_item.key].add(formatting_item)
            else:
                potential_formatting_items[formatting_item.key] = {formatting_item}

            # Every potential formatting inherits from the parent formatting.
            formatting = set(parent_formatting)
            # If the formatting item would conflict with a parent formatting item, allow
            #  the parent item to be overwritten.
            if formatting_item.key in parent_formatting_items:
                formatting.remove(parent_formatting_items[formatting_item.key])

            formatting.add(formatting_item)

            add_potential_formattings(
                formatting,
                keys=potential_formatting_items.keys() - {formatting_item.key},
            )

        def remove_potential_formatting_keys(formatting_keys: Iterable[str]):
            """Removes all formatting items with the specified keys from the
            `potential_formatting_items` and updates the `potential_formattings`
            accordingly.
            """

            nonlocal potential_formattings

            if not formatting_keys:
                return

            removed_formatting_items = set[FormattingItem]()
            for formatting_key in formatting_keys:
                removed_formatting_items |= potential_formatting_items.pop(
                    formatting_key
                )

            potential_formattings = {
                formatting
                for formatting in potential_formattings
                if not formatting & removed_formatting_items
            }

        def update_potential_formattings():
            """Updates the `potential_formattings` based on
            `components_with_potential_items` and `formattings_with_potential_items`.
            """

            # Remove any potential formattings that conflict with the subtuple's new
            #  components.

            remove_potential_formatting_keys(
                formatting_key
                for formatting_key in potential_formatting_items.keys()
                # A parent formatting key can never conflict with a component in the
                #  subtuple, so we can check that first as a shortcut.
                if formatting_key not in parent_formatting_items
                and any(
                    is_affected_by_inheriting(component, {formatting_key})
                    for component in components_with_potential_items
                )
            )

            components_with_potential_items.clear()

            # Add potential formattings present in the subtuple's new components.

            for formatting in formattings_with_potential_items:
                for formatting_item in formatting:
                    add_potential_formatting_item(formatting_item)

            formattings_with_potential_items.clear()

        for subtuple_end in range(subtuple_start + 1, len(formattings) + 1):
            subtuple = formattings[subtuple_start:subtuple_end]
            subtuple_components_start = subcomponent_start + subtuple_start
            subtuple_components_end = subcomponent_start + subtuple_end
            subtuple_components = subcomponents[
                subtuple_components_start:subtuple_components_end
            ]

            # Since the length of the subtuple starts at 1 and increases by 1 each
            #  iteration, every element in the subtuple is `subtuple[-1]` at some point,
            #  so this covers everything in the subtuple.
            formattings_with_potential_items.add(subtuple[-1])
            # The same applies here.
            components_with_potential_items.append(subtuple_components[-1])

            remainder_factoring = factor_and_get_cost(
                formattings[subtuple_end:],
                parent_formatting,
                subcomponent_start + subtuple_end,
            )
            if remainder_factoring.cost >= best_cost:
                continue

            if len(subtuple) == 1:
                # If the subtuple only has one element, it's unnecessary to compute and
                #  try all the `potential_formattings`.
                formattings_to_try = {subtuple[0]}
            else:
                update_potential_formattings()
                formattings_to_try = potential_formattings

            for formatting in formattings_to_try:
                subtuple_formatting = formatting - parent_formatting

                cost = get_cost(subtuple_formatting) + remainder_factoring.cost
                if cost >= best_cost:
                    continue

                subtuple_factoring = factor_and_get_cost(
                    subtuple, formatting, subcomponent_start + subtuple_start
                )
                cost += subtuple_factoring.cost
                if cost >= best_cost:
                    continue

                best_cost = cost
                best_subtuple_formatting = subtuple_formatting
                best_subtuple_factoring = subtuple_factoring
                best_remainder_factoring = remainder_factoring

        # The above loop must have ran for at least one iteration.
        assert best_subtuple_formatting is not None
        assert best_subtuple_factoring is not None
        assert best_remainder_factoring is not None

        return FactoredFormattings(
            value=[
                *parent_formattings,
                [best_subtuple_formatting, *best_subtuple_factoring.value],
                *best_remainder_factoring.value,
            ],
            cost=best_cost,
        )

    subcomponent_iterator = iter(subcomponents)

    def get_factored_component(
        factoring: FactoredFormattingList,
    ) -> FactoredTextComponent:
        """Converts a `FactoredFormattingList` to a `TextComponent`."""

        formatting = get_component_formatting(cast(FormattingSet, factoring[1]))
        contents = cast(list[ellipsis | FactoredFormattingList], factoring[1:])

        if contents == [...]:
            return reduce(
                set_component_formatting(next(subcomponent_iterator), formatting)
            )

        formatting_with_text = cast(TextComponentTextDict, {"text": ""} | formatting)
        output: list[FactoredTextComponent] = [formatting_with_text]

        flat_subcomponents = list[FlatTextComponent]()

        def end_flat_subcomponents():
            if not flat_subcomponents:
                return

            output.extend(merged(reduced(flat_subcomponents)))

            flat_subcomponents.clear()

        for item in contents:
            if item is ...:
                flat_subcomponents.append(next(subcomponent_iterator))
                continue

            subcomponent = get_factored_component(item)  # type: ignore

            if isinstance(subcomponent, list):
                end_flat_subcomponents()

                output.append(subcomponent)
                continue

            flat_subcomponents.append(subcomponent)

        end_flat_subcomponents()

        if len(output) == 1:
            return output[0]

        return output

    return get_factored_component(
        factor_and_get_cost(
            formattings=tuple(
                get_formatting_items(subcomponent) for subcomponent in subcomponents
            ),
            parent_formatting=FormattingSet(),
        ).value
    )
