from typing import Literal, TypedDict

from typing_extensions import NotRequired, Required

TextComponentText = str | int | float | bool


class TextComponentChildren(TypedDict, total=False):
    extra: list["TextComponent"]


class TextComponentClickEvent(TypedDict):
    action: (
        Literal["open_url"]
        | Literal["open_file"]
        | Literal["run_command"]
        | Literal["suggest_command"]
        | Literal["change_page"]
        | Literal["copy_to_clipboard"]
    )
    value: str


class TextComponentItem(TypedDict):
    id: str
    count: NotRequired[int]
    tag: NotRequired[str]


class TextComponentEntity(TypedDict, total=False):
    name: "TextComponent"
    type: Required[str]
    id: Required[str]


class TextComponentShowTextHoverEvent(TypedDict):
    action: Literal["show_text"]
    contents: "TextComponent"


class TextComponentShowItemHoverEvent(TypedDict):
    action: Literal["show_item"]
    contents: TextComponentItem


class TextComponentShowEntityHoverEvent(TypedDict):
    action: Literal["show_entity"]
    contents: TextComponentEntity


TextComponentHoverEvent = (
    TextComponentShowTextHoverEvent
    | TextComponentShowItemHoverEvent
    | TextComponentShowEntityHoverEvent
)


class TextComponentFormatting(TypedDict, total=False):
    color: str
    font: str
    bold: bool
    italic: bool
    underlined: bool
    strikethrough: bool
    obfuscated: bool
    insertion: str
    clickEvent: TextComponentClickEvent
    hoverEvent: TextComponentHoverEvent


class TextComponentDictBase(TextComponentChildren, TextComponentFormatting):
    pass


class TextComponentTextDict(TextComponentDictBase):
    text: TextComponentText


class TextComponentTranslationDict(
    # This is necessary because `with` is a reserved keyword.
    TypedDict(
        "TranslatedTextComponentDictWith",
        {"with": NotRequired[list["TextComponent"]]},
    ),
    TextComponentDictBase,
):
    translate: str


class TextComponentScore(TypedDict):
    name: str
    objective: str
    value: NotRequired[str]


class TextComponentScoreDict(TextComponentDictBase):
    score: TextComponentScore


class TextComponentSelectorDict(TextComponentDictBase, total=False):
    selector: Required[str]
    separator: "TextComponent"


class TextComponentKeybindDict(TextComponentDictBase):
    keybind: str


class TextComponentDictNBTBase(TextComponentDictBase, total=False):
    nbt: Required[str]
    interpret: bool
    separator: "TextComponent"


class TextComponentBlockNBTDict(TextComponentDictNBTBase):
    block: str


class TextComponentEntityNBTDict(TextComponentDictNBTBase):
    entity: str


class TextComponentStorageNBTDict(TextComponentDictNBTBase):
    storage: str


TextComponentNBTDict = (
    TextComponentBlockNBTDict | TextComponentEntityNBTDict | TextComponentStorageNBTDict
)

TextComponentDict = (
    TextComponentTextDict
    | TextComponentTranslationDict
    | TextComponentScoreDict
    | TextComponentSelectorDict
    | TextComponentKeybindDict
    | TextComponentNBTDict
)

TextComponent = TextComponentText | TextComponentDict | list["TextComponent"]

# This isn't completely flat, since it still allows for `extra`, but it's as close as we
#  can practically get.
FlatTextComponent = TextComponentText | TextComponentDict
