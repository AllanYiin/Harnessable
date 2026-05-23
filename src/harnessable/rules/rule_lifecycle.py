from __future__ import annotations

from enum import Enum


class RuleLifecycle(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    SHADOW = "SHADOW"
    ARCHIVED = "ARCHIVED"
