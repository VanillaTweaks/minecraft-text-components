from .flat import flat
from .formatting import get_formatting_keys, is_affected_by_inheriting
from .types import TextComponent


def prevent_inheritance(components: list[TextComponent]):
    """If necessary to prevent the inputted list's other components from inheriting
    formatting from the first, returns a copy of the list with `""` inserted at the
    start.

    Otherwise, returns the original list.
    """

    component_iterator = iter(components)

    try:
        first_component = next(component_iterator)
    except StopIteration:
        return components

    formatting_keys = get_formatting_keys(first_component)

    if not formatting_keys:
        return components

    for component in component_iterator:
        for flat_component in flat(component):
            if is_affected_by_inheriting(flat_component, formatting_keys):
                return ["", *components]

    return components
