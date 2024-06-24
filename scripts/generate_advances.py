import json
import math
from typing import Literal, NotRequired, TypedDict

import requests
from PIL import Image


class SpaceFontProvider(TypedDict):
    type: Literal["space"]
    advances: dict[str, int]


class BitmapFontProvider(TypedDict):
    type: Literal["bitmap"]
    file: str
    height: NotRequired[int]
    ascent: int
    chars: list[str]


class LegacyUnicodeFontProvider(TypedDict):
    type: Literal["legacy_unicode"]
    sizes: str
    template: str


class TTFFontProvider(TypedDict):
    type: Literal["ttf"]
    file: str
    shift: list[float]
    size: float
    oversample: float
    skip: str | list[str]


FontProvider = (
    SpaceFontProvider | BitmapFontProvider | LegacyUnicodeFontProvider | TTFFontProvider
)


class Font(TypedDict):
    providers: list[FontProvider]


print("Generating advances...")

# A range of all 16-bit code points.
LEGACY_UNICODE = range(0xFFFF + 1)
# A range of all surrogate code points.
SURROGATES = range(0xD800, 0xDFFF + 1)

# The width of the space between glyphs in in-game pixels.
KERNING_WIDTH = 1
# The default height of a bitmap font glyph in in-game pixels.
DEFAULT_GLYPH_HEIGHT = 8

# A mapping from each character to its advance amount in in-game pixels, excluding code
# points only covered by the legacy unicode font.
advances: dict[str, int] = {}
# A mapping from each legacy unicode font character to its advance amount in in-game
# pixels, excluding ones already covered by `advances`.
legacy_unicode_advances: dict[str, int] = {}

session = requests.Session()

ASSETS = "https://raw.githubusercontent.com/misode/mcmeta/assets/assets/minecraft"

font: Font = session.get(f"{ASSETS}/font/default.json").json()

for provider in font["providers"]:
    if provider["type"] == "space":
        advances |= provider["advances"]

    elif provider["type"] == "bitmap":
        texture_url = f"{ASSETS}/textures/{provider['file'].partition(':')[2]}"
        texture = Image.open(session.get(texture_url, stream=True).raw)

        row_count = len(provider["chars"])
        column_count = len(provider["chars"][0])

        row_height = texture.height // row_count
        column_width = texture.width // column_count

        glyph_height = provider.get("height", DEFAULT_GLYPH_HEIGHT)
        glyph_scale = glyph_height / row_height

        for row_index in range(row_count):
            row = provider["chars"][row_index]
            for column_index in range(column_count):
                char = row[column_index]

                if char in {"\u0000", "\u0020"}:
                    # These characters are ignored in bitmap font providers.
                    continue

                glyph_x = column_index * column_width
                glyph_y = row_index * row_height

                def get_glyph_width():
                    # Find the first non-empty column of pixels from the right within
                    # the glyph.
                    for x in reversed(range(column_width)):
                        for y in range(row_height):
                            if texture.getpixel(  # type: ignore
                                (glyph_x + x, glyph_y + y)
                            )[3]:
                                return x + 1
                    return 0

                glyph_width = get_glyph_width()

                # For negative `glyph_scale`s, it makes no sense to add 0.5 and then
                # truncate instead of rounding, but it's straight from the game's code,
                # so we're going with it.
                advance = math.trunc(glyph_width * glyph_scale + 0.5) + KERNING_WIDTH

                advances[char] = advance

    elif provider["type"] == "legacy_unicode":
        sizes_url = f"{ASSETS}/{provider['sizes'].partition(':')[2]}"
        sizes = session.get(sizes_url).content

        for char_code in LEGACY_UNICODE:
            if char_code in SURROGATES:
                continue

            char = chr(char_code)

            if char in advances:
                # Skip characters already covered by other font providers.
                continue

            # A byte with the start position of the character in the left half and the
            # end position in the right half.
            size = sizes[char_code]
            char_start = size >> 4
            char_end = (size & 0xF) + 1

            advance = (char_end - char_start) // 2 + KERNING_WIDTH
            legacy_unicode_advances[char] = advance

    else:
        raise NotImplementedError(
            f"Provider type {repr(provider['type'])} is not currently supported (but "
            "should be if you're seeing this error)"
        )


def write_json(filename: str, advances: dict[str, int]):
    with open(f"data/{filename}.json", "w", encoding="utf-8") as file:
        json.dump(
            dict(sorted(advances.items())),
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


write_json("advances", advances)
write_json("legacy_unicode_advances", legacy_unicode_advances)

print("Done!")
