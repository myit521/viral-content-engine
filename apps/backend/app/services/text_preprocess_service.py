from __future__ import annotations

import html
import re
from dataclasses import dataclass


_TAG_RE = re.compile(r"<[^>]+>")
_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_LIST_ITEM_RE = re.compile(r"^\s*[-*]\s+", re.MULTILINE)


@dataclass
class PreprocessResult:
    cleaned_text: str
    markdown_text: str
    segments: list[str]


class TextPreprocessService:
    def __init__(self, max_segment_length: int = 900) -> None:
        self.max_segment_length = max_segment_length

    def clean_html(self, raw_text: str) -> str:
        if not raw_text:
            return ""
        text = html.unescape(raw_text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = _TAG_RE.sub(" ", text)
        text = _MULTI_SPACE_RE.sub(" ", text)
        text = _MULTI_NEWLINE_RE.sub("\n\n", text)
        return text.strip()

    def to_markdown(self, cleaned_text: str) -> str:
        if not cleaned_text:
            return ""
        lines = [line.strip() for line in cleaned_text.splitlines()]
        lines = [line for line in lines if line]
        normalized = "\n\n".join(lines)
        normalized = _LIST_ITEM_RE.sub("- ", normalized)
        return normalized.strip()

    def split_segments(self, markdown_text: str) -> list[str]:
        if not markdown_text:
            return []
        chunks: list[str] = []
        current = ""
        paragraphs = [p.strip() for p in markdown_text.split("\n\n") if p.strip()]
        for paragraph in paragraphs:
            if len(paragraph) > self.max_segment_length:
                for i in range(0, len(paragraph), self.max_segment_length):
                    part = paragraph[i : i + self.max_segment_length].strip()
                    if part:
                        if current:
                            chunks.append(current.strip())
                            current = ""
                        chunks.append(part)
                continue
            if not current:
                current = paragraph
            elif len(current) + 2 + len(paragraph) <= self.max_segment_length:
                current = f"{current}\n\n{paragraph}"
            else:
                chunks.append(current.strip())
                current = paragraph
        if current:
            chunks.append(current.strip())
        return chunks

    def preprocess(self, raw_text: str) -> PreprocessResult:
        cleaned = self.clean_html(raw_text)
        markdown_text = self.to_markdown(cleaned)
        segments = self.split_segments(markdown_text)
        return PreprocessResult(
            cleaned_text=cleaned,
            markdown_text=markdown_text,
            segments=segments,
        )


text_preprocess_service = TextPreprocessService()
