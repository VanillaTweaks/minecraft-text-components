from .advances import get_advance
from .container import container
from .pad_each_line import pad_each_line
from .types import TextComponent


def center(component: TextComponent):
    """Centers a text component, automatically minified."""

    return pad_each_line(component, lambda advance: (container.width - advance) / 2)


def right(component: TextComponent):
    """Right-aligns a text component, automatically minified."""

    return pad_each_line(component, lambda advance: container.width - advance)


def local_center(component: TextComponent):
    """Centers a text component using its own width as the container width,
    automatically minified.
    """

    with container(get_advance(component)):
        return center(component)


def local_right(component: TextComponent):
    """Right-aligns a text component using its own width as the container width,
    automatically minified.
    """

    with container(get_advance(component)):
        return right(component)
