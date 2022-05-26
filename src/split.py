from collections.abc import Callable, Generator
from re import Pattern
from typing import cast, overload

from .flat import flat
from .types import (
    FlatTextComponent,
    TextComponent,
    TextComponentDict,
    TextComponentText,
)

UncallableSeparator = str | None | Pattern[str]
CallableSeparator = Callable[[str], list[str]]
Separator = UncallableSeparator | CallableSeparator

SplitComponent = FlatTextComponent | list[FlatTextComponent]


def split_text(
    component: TextComponentText,
    sep: Separator = None,
    maxsplit: int = -1,
):
    component = str(component)

    if callable(sep):
        split_component = sep(component)
    elif isinstance(sep, Pattern):
        split_component = [
            # Ensure `None` is never returned.
            subcomponent or ""
            for subcomponent in cast(list[str | None], sep.split(component, maxsplit))
        ]
    else:
        split_component = component.split(sep, maxsplit)

    # Ensure an empty list is never returned.
    return split_component or [""]


@overload
def split(
    component: TextComponent,
    sep: UncallableSeparator = None,
    maxsplit: int = -1,
) -> Generator[SplitComponent, None, None]:
    ...


@overload
def split(
    component: TextComponent,
    sep: CallableSeparator,
) -> Generator[SplitComponent, None, None]:
    ...


def split(
    component: TextComponent,
    sep: Separator = None,
    maxsplit: int = -1,
):
    """Generates the sequence of subcomponents split from a specified text component.

    Always yields at least one value.
    """

    previous_subcomponent: SplitComponent | None = None

    def append_to_previous_subcomponent(subcomponent: FlatTextComponent):
        nonlocal previous_subcomponent

        if previous_subcomponent is None:
            previous_subcomponent = subcomponent

        elif isinstance(previous_subcomponent, list):
            previous_subcomponent.append(subcomponent)

        else:
            previous_subcomponent = ["", previous_subcomponent, subcomponent]

    for subcomponent in flat(component):
        if isinstance(subcomponent, dict):
            if "text" not in subcomponent:
                # We can't split something without text.
                append_to_previous_subcomponent(subcomponent)
                continue

            substrings = split_text(subcomponent["text"], sep, maxsplit)
            split_subcomponent = [
                cast(TextComponentDict, {**subcomponent, "text": substring})
                for substring in substrings
            ]

        else:
            split_subcomponent = split_text(subcomponent, sep, maxsplit)

        for i, split_subcomponent_item in enumerate(split_subcomponent):
            if i == 0:
                append_to_previous_subcomponent(split_subcomponent_item)
                continue

            yield cast(SplitComponent, previous_subcomponent)
            previous_subcomponent = split_subcomponent_item

    yield previous_subcomponent or ""
