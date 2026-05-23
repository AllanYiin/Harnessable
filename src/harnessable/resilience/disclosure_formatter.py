from __future__ import annotations


class DisclosureFormatter:
    def format(self, step: object, default: str = "The request was completed with reduced capability.") -> str:
        disclosure = getattr(step, "disclosure", None) or {}
        return disclosure.get("template") or disclosure.get("message") or default
