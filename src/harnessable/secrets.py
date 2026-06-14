from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Protocol


class SecretProvider(Protocol):
    def get(self, name: str) -> str | None: ...


@dataclass(frozen=True)
class StaticSecretProvider:
    values: dict[str, str] = field(default_factory=dict)

    def get(self, name: str) -> str | None:
        return self.values.get(name)


@dataclass(frozen=True)
class EnvSecretProvider:
    prefix: str = ""

    def get(self, name: str) -> str | None:
        key = f"{self.prefix}{name}" if self.prefix else name
        return os.environ.get(key)
