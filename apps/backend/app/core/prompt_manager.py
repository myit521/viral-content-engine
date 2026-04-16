from __future__ import annotations

import re
from pathlib import Path

from app.core.settings import ai_settings


class PromptNotFoundError(FileNotFoundError):
    pass


class PromptVariableError(ValueError):
    pass


class PromptManager:
    _pattern = re.compile(r"\{\{\s*(?P<braced>[a-zA-Z0-9_]+)\s*\}\}|\{(?P<plain>[a-zA-Z0-9_]+)\}")

    def __init__(self, prompt_root: str | Path | None = None) -> None:
        self.prompt_root = Path(prompt_root or ai_settings.prompt_root)

    def resolve_path(self, prompt_id: str, version: str | None = None) -> Path:
        if prompt_id.endswith(".md"):
            candidate = self.prompt_root / prompt_id
            if candidate.exists():
                return candidate

        if version and prompt_id.endswith(f".{version}"):
            candidate = self.prompt_root / f"{prompt_id}.md"
            if candidate.exists():
                return candidate

        if version:
            candidate = self.prompt_root / f"{prompt_id}.{version}.md"
            if candidate.exists():
                return candidate

        candidate = self.prompt_root / f"{prompt_id}.md"
        if candidate.exists():
            return candidate

        raise PromptNotFoundError(
            f"Prompt '{prompt_id}' with version '{version}' was not found under '{self.prompt_root}'."
        )

    def load_template(self, prompt_id: str, version: str | None = None) -> str:
        prompt_path = self.resolve_path(prompt_id, version)
        return prompt_path.read_text(encoding="utf-8")

    def render(self, template_text: str, variables: dict[str, object] | None = None) -> str:
        data = {key: "" if value is None else str(value) for key, value in (variables or {}).items()}
        missing_keys: set[str] = set()

        def replace(match: re.Match[str]) -> str:
            key = match.group("braced") or match.group("plain") or ""
            if key not in data:
                missing_keys.add(key)
                return match.group(0)
            return data[key]

        rendered = self._pattern.sub(replace, template_text)
        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise PromptVariableError(f"Missing prompt variables: {missing}")
        return rendered

    def load(
        self,
        prompt_id: str,
        version: str | None = None,
        variables: dict[str, object] | None = None,
    ) -> str:
        return self.render(self.load_template(prompt_id, version), variables)


prompt_manager = PromptManager()
