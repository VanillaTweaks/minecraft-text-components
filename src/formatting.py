from .types import TextComponent, TextComponentFormatting

FORMATTING_KEYS = frozenset(TextComponentFormatting.__annotations__.keys())


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
