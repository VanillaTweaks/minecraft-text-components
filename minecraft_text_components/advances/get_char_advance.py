import json
from functools import cache
from importlib import resources

from ..types import TextComponentFormatting

# The advance in in-game pixels added to a non-legacy-unicode character when bold.
BOLD_ADVANCE = 1.0
# The advance in in-game pixels added to a legacy unicode character when bold.
BOLD_LEGACY_UNICODE_ADVANCE = 0.5

# The advance of an unknown character in in-game pixels.
UNKNOWN_CHAR_ADVANCE = 6.0
# The advance of an invalid character (i.e. a lone surrogate) in in-game pixels.
INVALID_CHAR_ADVANCE = 8.0


@cache
def get_advances(filename: str) -> dict[str, int]:
    path = resources.files("minecraft_text_components") / f"resources/{filename}.json"
    return json.loads(path.read_text("utf8"))


def get_char_advance(
    char: str,
    formatting: TextComponentFormatting | None = None,
) -> float:
    """Gets the number of in-game pixels that a character takes up horizontally.

    ⚠️ Assumes the input is a string with length 1.
    """

    if formatting is None:
        formatting = {}

    # Whether the `char` only exists in the legacy unicode font.
    legacy_unicode = False
    advance = None

    advances = get_advances("advances")
    if char in advances:
        advance = float(advances[char])

    else:
        legacy_unicode_advances = get_advances("legacy_unicode_advances")
        if char in legacy_unicode_advances:
            legacy_unicode = True
            advance = float(legacy_unicode_advances[char])

        else:
            # The `char` is unknown or invalid.
            try:
                char.encode("utf-8")

                # The `char` is unknown.
                advance = UNKNOWN_CHAR_ADVANCE

            except UnicodeEncodeError:
                # The `char` is invalid.
                advance = INVALID_CHAR_ADVANCE

    if formatting.get("bold") == True:
        advance += BOLD_LEGACY_UNICODE_ADVANCE if legacy_unicode else BOLD_ADVANCE

    return advance
