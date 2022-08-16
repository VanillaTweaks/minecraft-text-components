import re

from .advances import get_line_advance
from .container import container
from .minify import minify
from .split import split
from .types import TextComponent

SPACES_PATTERN = re.compile(r"/( )/")


def wrap(component: TextComponent):
    """Inserts line breaks in a text component where there would otherwise be wrapping
    due to the text overflowing the container, automatically minified.
    """

    output: list[TextComponent] = []
    output_line: list[TextComponent] = []
    # Start each word with `""` to prevent unwanted inheritence.
    output_word: list[TextComponent] = [""]
    output_line_advance = 0
    output_word_advance = 0

    def end_line():
        """Appends the `output_line` to the `output`, and then resets the `output_line`
        and `output_line_advance`.
        """

        nonlocal output_line, output_line_advance

        if output:
            output.append("\n")
        output.append(output_line)

        output_line = []
        output_line_advance = 0

    def end_word(word_sep: TextComponent | None = None):
        """Appends the `output_word` to the `output_line`, and then resets the
        `output_word` and `output_word_advance`.
        """

        nonlocal output_word, output_word_advance

        if word_sep is not None and output_line:
            output_line.append(word_sep)
        output_line.append(output_word)

        output_word = [""]
        output_word_advance = 0

    for line in split(component, "\n"):
        words_and_spaces = split(line, SPACES_PATTERN)

        space: TextComponent | None = None
        for i, word_or_space in enumerate(words_and_spaces):

            if i % 2 == 0:
                word = word_or_space

                for char in split(
                    word,
                    # Starting with `""` ensures every input (e.g. `["ab", "cd"]`) is
                    #  split into a list in which each item has at most one character
                    #  (e.g. `["", "a", ["", "b", ""], "c", "d"]`) rather than a list in
                    #  which some items have multiple characters (e.g.
                    #  `["a", ["", "b", "c"], "d"]`), since the first item in any list
                    #  returned from this lambda can be appended to the previous item in
                    #  the `split` output.
                    lambda value: ["", *value],
                ):
                    # `char` either is empty or has only a single character.

                    char_advance = get_line_advance(char)
                    output_word_advance += char_advance
                    if output_word_advance > container.width:
                        # Wrap this character to the next line, breaking the word.

                        end_word()
                        end_line()
                        output_line_advance = output_word_advance = char_advance

                    else:
                        output_line_advance += char_advance
                        if output_line_advance > container.width:
                            # Wrap this word to the next line, NOT breaking the word.

                            end_line()
                            output_line_advance = output_word_advance

                    output_word.append(char)

                end_word(word_sep=space)

            else:
                space = word_or_space

                output_line_advance += get_line_advance(space)

        end_line()

    return minify(output)
