from collections.abc import Generator

from .formatting import get_formatting
from .types import (
    TextComponent,
    TextComponentDict,
    TextComponentFormatting,
    TextComponentText,
)


def flat(
    component: TextComponent,
    # Formatting for the component and its children to inherit.
    formatting: TextComponentFormatting = {},
) -> Generator[TextComponentText | TextComponentDict, None, None]:
    """Generates the sequence of `TextComponentText`s and `TextComponentDict`s needed to
    recursively flatten all arrays and `extra` properties of a text component into one
    big array.

    Never yields `''`. It's safe to shallowly mutate any yielded object. Doesn't
    transform `with` properties at all.
    """

    formatting |= get_formatting(component)

    if isinstance(component, list):
        if component:
            for subcomponent in component:
                yield from flat(subcomponent, formatting)

        return

    if isinstance(component, dict):
        component_without_extra: TextComponentDict = component.copy()
        extra = component_without_extra.pop("extra", None)

        yield component_without_extra | formatting  # type: ignore

        if extra:
            for subcomponent in extra:
                yield from flat(subcomponent, formatting)

        return

    if component == "":
        return

    if formatting:
        yield {"text": component, **formatting}  # type: ignore

        return

    yield component
