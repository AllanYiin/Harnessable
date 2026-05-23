from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, TypeVar


TEnum = TypeVar("TEnum", bound=Enum)


def enum_value(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


def parse_enum(enum_type: type[TEnum], value: Any) -> TEnum:
    if isinstance(value, enum_type):
        return value
    return enum_type(str(value))


def to_plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {k: to_plain(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {k: to_plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_plain(v) for v in value]
    return value


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
