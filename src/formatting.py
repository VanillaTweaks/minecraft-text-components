from collections.abc import Collection

from .regex import LINE_BREAKS
from .types import FlatTextComponent, TextComponent, TextComponentFormatting

FORMATTING_KEYS = frozenset(TextComponentFormatting.__annotations__.keys())

WHITESPACE_UNAFFECTED_BY_KEYS = frozenset({"color", "italic"})
WHITESPACE_AFFECTED_BY_KEYS = FORMATTING_KEYS - WHITESPACE_UNAFFECTED_BY_KEYS


def get_formatting(component: TextComponent) -> TextComponentFormatting:
    """Gets a `TextComponentFormatting` with only the properties of the inputted
    component that can be inherited by other text components.
    """

    if isinstance(component, list):
        return get_formatting(component[0])

    formatting: TextComponentFormatting = {}

    if isinstance(component, dict):
        for key in FORMATTING_KEYS:
            if key in component:
                formatting[key] = component[key]

    return formatting


def is_affected_by_inheriting(component: FlatTextComponent, keys: Collection[str]):
    """Checks whether inheriting the specified formatting keys would have a
    distinguishable in-game effect on the specified `FlatTextComponent`.
    """

    if len(keys) == 0:
        return False

    text: str | None = None

    if isinstance(component, dict):
        if "text" in component:
            text = str(component["text"])
    else:
        text = str(component)

    text_is_whitespace = False

    if text is not None:
        if text == "":
            return False

        text_is_whitespace = text.isspace()

        if text_is_whitespace and LINE_BREAKS.match(text):
            # Nothing affects line breaks.
            return False

    if isinstance(component, dict):
        # Check if any formatting key that affects this component is missing from the
        #  component, in which case the component would inherit it.

        if text_is_whitespace:
            # Ignore the keys that don't affect whitespace.
            keys = set(keys) - WHITESPACE_UNAFFECTED_BY_KEYS

        return any(key not in component for key in keys)

    if text_is_whitespace:
        return any(key in WHITESPACE_AFFECTED_BY_KEYS for key in keys)

    # Plain non-whitespace text is affected by any formatting.
    return True


def is_affected_by_inheriting_from(component: FlatTextComponent, parent: TextComponent):
    """Checks whether inheriting the specified formatting from a parent `TextComponent`
    would have a distinguishable in-game effect on the specified `FlatTextComponent`.
    """

    return is_affected_by_inheriting(component, get_formatting(parent))
