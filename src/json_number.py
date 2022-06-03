import inspect
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from inspect import Parameter
from types import UnionType
from typing import Any, Final

JSON_NUMBER_PATTERN = re.compile(r"^\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?$", re.ASCII)


@dataclass
class JSONNumber:
    value: Final[str]

    def __post_init__(self):
        if not JSONNumber.is_valid(self.value):
            raise ValueError(
                f"The following value is not a valid JSON number: {repr(self.value)}"
            )

    @classmethod
    def is_valid(cls, value: str):
        return JSON_NUMBER_PATTERN.match(value) is not None

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


make_iterencode: Callable[..., Any] = json.encoder._make_iterencode  # type: ignore

make_iterencode_default_parameters = tuple(
    parameter
    for parameter in inspect.signature(make_iterencode).parameters.values()
    if parameter.default is not Parameter.empty
)


def patch_make_iterencode_default(i: int, default: object):
    parameter = make_iterencode_default_parameters[i]

    if parameter.name == "isinstance":
        # Replace `isinstance`.

        def patched_isinstance(
            __obj: object,
            __class_or_tuple: (
                type | UnionType | tuple[type | UnionType | tuple[Any, ...], ...]
            ),
        ) -> bool:
            if isinstance(__obj, JSONNumber) and __class_or_tuple is int:
                # Make `_make_iterencode` think `JSONNumber`s are `int`s so it calls
                #  `patched_int_repr` to encode them.
                return True

            return default(__obj, __class_or_tuple)  # type: ignore

        return patched_isinstance

    if parameter.name == "_intstr":
        # Replace `int.__repr__`.

        def patched_int_repr(self: int) -> str:
            if isinstance(self, JSONNumber):
                # Encode `JSONNumber`s using their `repr`.
                return repr(self)

            return default(self)  # type: ignore

        return patched_int_repr

    return default


# Apply the monkey patches.
make_iterencode.__defaults__ = tuple(
    patch_make_iterencode_default(i, default)
    for i, default in enumerate(make_iterencode.__defaults__)
)
