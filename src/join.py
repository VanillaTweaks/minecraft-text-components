from .types import TextComponent


def join(components: list[TextComponent], sep: TextComponent):
    """Concatenates a list of text components into one text component."""

    joined_component: list[TextComponent] = [""]

    for i, component in enumerate(components):
        if i != 0:
            joined_component.append(sep)

        joined_component.append(component)

    return joined_component
