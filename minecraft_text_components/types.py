from typing import Literal, TypedDict, final

from typing_extensions import NotRequired, Required

TextComponentText = str | int | float | bool


class TextComponentChildren(TypedDict, total=False):
    extra: list["TextComponent"]


@final
class TextComponentClickEvent(TypedDict):
    action: (
        Literal["open_url"]
        | Literal["open_file"]
        | Literal["run_command"]
        | Literal["suggest_command"]
        | Literal["change_page"]
        | Literal["copy_to_clipboard"]
    )
    value: TextComponentText


@final
class TextComponentItem(TypedDict):
    id: str
    count: NotRequired[int]
    tag: NotRequired[str]


@final
class TextComponentEntity(TypedDict, total=False):
    name: "TextComponent"
    type: Required[str]
    id: Required[str]


@final
class TextComponentShowTextHoverEvent(TypedDict):
    action: Literal["show_text"]
    contents: "TextComponent"


@final
class TextComponentShowItemHoverEvent(TypedDict):
    action: Literal["show_item"]
    contents: TextComponentItem


@final
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
    insertion: TextComponentText
    clickEvent: TextComponentClickEvent
    hoverEvent: TextComponentHoverEvent


class TextComponentDictBase(TextComponentChildren, TextComponentFormatting):
    pass


@final
class TextComponentTextDict(TextComponentDictBase):
    text: TextComponentText


@final
class TextComponentTranslationDict(
    # This is necessary because `with` is a reserved keyword.
    TypedDict(
        "TranslatedTextComponentDictWith",
        {"with": NotRequired[list["TextComponent"]]},
    ),
    TextComponentDictBase,
):
    translate: str


@final
class TextComponentScore(TypedDict):
    name: str
    objective: str
    value: NotRequired[str]


@final
class TextComponentScoreDict(TextComponentDictBase):
    score: TextComponentScore


@final
class TextComponentSelectorDict(TextComponentDictBase, total=False):
    selector: Required[str]
    separator: "TextComponent"


@final
class TextComponentKeybindDict(TextComponentDictBase):
    keybind: str


class TextComponentDictNBTBase(TextComponentDictBase, total=False):
    nbt: Required[str]
    interpret: bool
    separator: "TextComponent"


@final
class TextComponentBlockNBTDict(TextComponentDictNBTBase):
    block: str


@final
class TextComponentEntityNBTDict(TextComponentDictNBTBase):
    entity: str


@final
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

# Objects of this type should be completely flat and never have an `extra` key, even
#  though this type does not (and practically cannot) enforce that.
FlatTextComponent = TextComponentText | TextComponentDict
