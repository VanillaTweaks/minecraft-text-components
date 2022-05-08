# A range of char codes for every surrogate code point.
import json
from functools import cache

# The advance in in-game pixels added to a non-legacy-unicode code point when bold.
BOLD_ADVANCE = 1.0
# The advance in in-game pixels added to a legacy unicode code point when bold.
BOLD_LEGACY_UNICODE_ADVANCE = 0.5

# The advance of an unknown code point in in-game pixels.
UNKNOWN_CODE_POINT_ADVANCE = 6.0
# The advance of an invalid code point (i.e. a lone surrogate) in in-game pixels.
INVALID_CODE_POINT_ADVANCE = 8.0


@cache
def get_advances(filename: str) -> dict[str, int]:
    with open(f"{__file__}/../../data/{filename}.json", encoding="utf-8") as file:
        return json.load(file)


def get_code_point_advance(code_point: str, *, bold: bool = False) -> float:
    """Gets the number of in-game pixels that a code point takes up horizontally.

    ⚠️ Assumes the input is exactly one code point (and also not a line break).
    """

    # Whether the code point only exists in the legacy unicode font.
    legacy_unicode = False
    advance = None

    advances = get_advances("advances")
    if code_point in advances:
        advance = float(advances[code_point])

    else:
        legacy_unicode_advances = get_advances("legacy_unicode_advances")
        if code_point in legacy_unicode_advances:
            legacy_unicode = True
            advance = float(legacy_unicode_advances[code_point])

        else:
            # The `code_point` is unknown or invalid.
            try:
                code_point.encode("utf-8")

                # The `code_point` is unknown.
                advance = UNKNOWN_CODE_POINT_ADVANCE

            except UnicodeEncodeError:
                # The `code_point` is invalid.
                advance = INVALID_CODE_POINT_ADVANCE

    if bold:
        advance += BOLD_LEGACY_UNICODE_ADVANCE if legacy_unicode else BOLD_ADVANCE

    return advance
