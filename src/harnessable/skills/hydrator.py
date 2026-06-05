from __future__ import annotations

import re

from .schemas import HydratedSkill, SkillManifest, estimate_tokens


class SkillHydrator:
    def hydrate_summary(self, manifest: SkillManifest) -> HydratedSkill:
        text = self._read_skill(manifest)
        summary = _extract_sections(text, ["scope", "workflow overview", "routing boundaries"])
        if not summary:
            summary = _first_non_frontmatter_block(text, max_chars=2200)
        return HydratedSkill(
            manifest=manifest,
            content=summary,
            mode="summary",
            estimated_tokens=estimate_tokens(summary),
        )

    def hydrate_full(self, manifest: SkillManifest) -> HydratedSkill:
        text = self._read_skill(manifest)
        return HydratedSkill(
            manifest=manifest,
            content=text,
            mode="full",
            estimated_tokens=estimate_tokens(text),
        )

    def _read_skill(self, manifest: SkillManifest) -> str:
        path = manifest.resolved_path
        if path is None:
            raise FileNotFoundError(f"skill manifest has no path: {manifest.id}")
        return path.read_text(encoding="utf-8")


def _extract_sections(text: str, headings: list[str]) -> str:
    wanted = {item.lower() for item in headings}
    sections: list[str] = []
    matches = list(re.finditer(r"^(#{1,6})\s+(.+?)\s*$", text, flags=re.MULTILINE))
    for index, match in enumerate(matches):
        title = _normalize_heading(match.group(2))
        if title not in wanted:
            continue
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append(text[start:end].strip())
    return "\n\n".join(sections)


def _normalize_heading(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _first_non_frontmatter_block(text: str, max_chars: int) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            text = parts[2]
    return text.strip()[:max_chars]
