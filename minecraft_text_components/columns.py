from .advances import get_advance
from .advances import get_line_advance
from .container import container
from .overlap import overlap
from .pad_each_line import pad_each_line
from .types import TextComponent
from .whitespace import SPACE_ADVANCE, whitespace


def columns(*components: TextComponent):
    """Places a set of components into evenly spaced columns, each column being locally
    left-aligned, automatically minified.
    """

    component_advances: list[float] = []

    # The amount of in-game pixels available for additional columns in the container.
    free_width = container.width

    for component in components:
        component_advance = get_advance(component)
        component_advances.append(component_advance)

        free_width -= component_advance

    # Whether there should be whitespace to the left and right of all columns rather
    #  than only between columns.
    spacing_around_columns = True

    # The amount of whitespace around or between each column, rounded to the nearest
    #  valid whitespace width.
    column_spacing = free_width / (len(components) + 1)

    if column_spacing < SPACE_ADVANCE:
        # There isn't room to fit the spacing around columns, so try removing it.
        spacing_around_columns = False
        column_spacing = free_width / (len(components) - 1)

        if column_spacing < SPACE_ADVANCE:
            # There isn't room to fit any spacing between columns either.
            raise ValueError(
                "The specified columns are too wide to fit in the container."
            )

    # Round to the nearest valid whitespace advance.
    column_spacing = get_line_advance(whitespace(column_spacing))

    padded_columns: list[TextComponent] = []

    # The amount of whitespace to insert before the next component pushed to
    #  `padded_columns`.
    preceding_whitespace = 0

    if spacing_around_columns:
        preceding_whitespace += column_spacing

    for i, component in enumerate(components):
        padded_column = pad_each_line(component, preceding_whitespace)
        padded_columns.append(padded_column)

        component_advance = component_advances[i]
        preceding_whitespace += component_advance
        preceding_whitespace += column_spacing

    return overlap(*padded_columns)
