import re
from dataclasses import dataclass
from typing import Final

from .advances import get_line_advance
from .container import container
from .join import join
from .minify import minify
from .split import split
from .types import TextComponent
from .whitespace import whitespace

# The reason it's ` {2,}` instead of ` +` is because a single space in the middle of the
#  string is most likely just a normal space that should not be adjustable or allow
#  things to overlap it.
OVERLAPPABLE_WHITESPACE_PATTERN = re.compile(r"(^ +| {2,}| +$)")

# The maximum value that `whitespace_offset` is can be before additional
#  overflow correction attempts must be disallowed.
MAX_WHITESPACE_OFFSET = 4


@dataclass
class TextComponentRange:
    # The component in the range. Must not contain any whitespace.
    start: Final[float]
    # The horizontal position at which the component starts in in-game pixels.
    end: Final[float]
    # The horizontal position at which the component ends in in-game pixels.
    value: Final[TextComponent]


def overlap(*components: TextComponent):
    """Overlaps multiple text components as if they were rendered onto the same
    position, automatically minified.

    >>> overlap("t   t", "  t")
    "t t t"
    """

    # A list of lines, each line represented by a list of `TextComponentRange`s.
    range_lines: list[list[TextComponentRange]] = []

    # Construct all the ranges.
    for component in components:
        component_lines = split(component, "\n")

        for line_index, component_line in enumerate(component_lines):
            # Create the list in `range_lines` if it doesn't exist.
            if line_index >= len(range_lines):
                range_lines[line_index] = []

            range_line = range_lines[line_index]

            range_value: list[TextComponent] = []
            range_start = 0
            range_width = 0

            def end_range():
                """Ends the `range_value` inserts a range for it into the `range_line`
                (if the `range_value` was non-empty).
                """

                if not range_value:
                    return

                # The index in the `range_line` at which the new range containing the
                #  `range_value` should be inserted.
                range_index = 0

                for i, range in enumerate(range_line):
                    if range.start > range_start:
                        break

                    range_index = i

                def raise_collision_error(conflicting_subcomponent: TextComponent):
                    raise ValueError(
                        "The text components cannot be overlapped due to collision "
                        "between the following two subcomponents:\n"
                        f"{repr(minify(conflicting_subcomponent))}\n"
                        + repr(minify(range_value))
                    )

                if range_index != 0:
                    previous_range = range_line[range_index - 1]

                    if range_start < previous_range.end:
                        raise_collision_error(previous_range.value)

                range_end = range_start + range_width

                if range_index != len(range_line):
                    next_range = range_line[range_index]

                    if range_end > next_range.start:
                        raise_collision_error(next_range.value)

                range = TextComponentRange(range_start, range_end, range_value)
                range_line.insert(range_index, range)

            # The `component_line` split into a list in which odd indexes have
            #  whitespace-only segments and even indexes do not.
            subcomponents = split(component_line, OVERLAPPABLE_WHITESPACE_PATTERN)

            for i, subcomponent in enumerate(subcomponents):
                subcomponent_advance = get_line_advance(subcomponent)

                if i % 2 == 0:
                    # This subcomponent does not contain only whitespace, so add it to
                    #  the `range_value` if it isn't empty.

                    if subcomponent_advance:
                        range_value.append(subcomponent)
                        range_width += subcomponent_advance

                else:
                    # This subcomponent contains only whitespace, so end the
                    #  `range_value`.

                    end_range()

                    # Set up the next range.
                    range_start += range_width + subcomponent_advance
                    range_value = []
                    range_width = 0

            end_range()

    output_lines: list[TextComponent] = []

    for range_line in range_lines:
        # The amount (always negative) of in-game pixels to add to the whitespace in
        #  order to avoid the line overflowing the container.
        whitespace_offset = 0
        # The amount that `output_line`'s advance exceeds the container width.
        overflowing_advance = 0
        # Each range's original `whitespace_advance` value without offsets.
        initial_whitespace_advances: list[float] = []

        while True:
            # Attempt to construct the `output_line`.

            output_line: list[TextComponent] = [""]
            # The position in the line at which the previous range ended.
            previous_range_end = 0
            # The amount that whitespace advances still need to be offset in order to
            #  apply the full `whitespace_offset`.
            whitespace_offset_remaining = whitespace_offset

            for range_index, range in enumerate(range_line):
                ideal_whitespace_advance = max(
                    0, range.start - previous_range_end - whitespace_offset_remaining
                )
                whitespace_before_range = whitespace(ideal_whitespace_advance)

                output_line.append(whitespace_before_range)
                output_line.append(range.value)

                range_width = range.end - range.start
                whitespace_advance = get_line_advance(whitespace_before_range)
                previous_range_end += whitespace_advance + range_width

                if whitespace_offset == 0:
                    initial_whitespace_advances[range_index] = whitespace_advance
                elif whitespace_offset_remaining:
                    initial_whitespace_advance = initial_whitespace_advances[
                        range_index
                    ]
                    whitespace_offset_remaining = min(
                        0,
                        whitespace_offset_remaining
                        + initial_whitespace_advance
                        - whitespace_advance,
                    )

            overflowing_advance = previous_range_end - container.width
            if overflowing_advance <= 0:
                # The attempt was successful.
                break

            # The line overflows the container, so try again with more overflow
            #  correction.
            whitespace_offset -= 0.5

            if whitespace_offset > MAX_WHITESPACE_OFFSET:
                # No more attempts can be made, and the line still overflows.
                raise ValueError(
                    "The following text component cannot fit on one line:\n"
                    + repr(minify(output_line))
                )

        output_lines.append(output_line)

    return minify(join(output_lines, "\n"))
