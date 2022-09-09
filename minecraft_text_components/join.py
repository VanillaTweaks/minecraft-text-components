from collections.abc import Iterable

from .minify import minify
from .types import TextComponent


def join(sep: TextComponent, components: Iterable[TextComponent]):
    """Concatenates a list of text components into one text component, automatically
    minified.
    """

    joined_component: list[TextComponent] = [""]

    for i, component in enumerate(components):
        if i != 0:
            joined_component.append(sep)

        joined_component.append(component)

    return minify(joined_component)
