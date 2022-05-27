from .container import container
from .pad_each_line import pad_each_line
from .types import TextComponent


def center(component: TextComponent):
    return pad_each_line(component, lambda advance: (container.width - advance) / 2)
