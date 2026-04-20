from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.core.config import Settings
from app.models.schemas import CopyResult


def _short_excerpt(text: str, limit: int = 42) -> str:
    compact = re.sub(r"\s+", "", text)
    compact = re.sub(r"[《》\"“”'‘’]", "", compact)
    return compact[:limit]


class CopyProvider(ABC):
    @abstractmethod
    def generate(
        self,
        book_title: str,
        cleaned_text: str,
        style: str,
        cover_theme: str,
    ) -> CopyResult:
        raise NotImplementedError


class MockCopyProvider(CopyProvider):
    def generate(
        self,
        book_title: str,
        cleaned_text: str,
        style: str,
        cover_theme: str,
    ) -> CopyResult:
        style_name = style.strip() or "温柔陪伴"
        theme_name = cover_theme.strip() or "安静夜读"
        excerpt = _short_excerpt(cleaned_text)

        if book_title.strip():
            title = f"今晚读《{book_title.strip()}》"
            subtitle = f"{style_name}的一段文字"
            intro = f"晚上好，这里是序蓝酱。今天陪你读一段《{book_title.strip()}》。"
        else:
            title = "今晚，读一段安静的文字"
            subtitle = style_name
            intro = "晚上好，这里是序蓝酱。今天陪你读一段安静的文字。"

        description = (
            f"这是一段适合慢慢听的阅读内容。风格偏{style_name}，不急着解释，"
            f"只把文字本身放在你身边。摘句参考：{excerpt}..."
        )
        cover_text = "把心慢慢放回安静里"
        keywords = [style_name, theme_name, "序蓝酱", "读书陪伴"]
        outro = "读到这里就好。愿你今晚可以轻一点，慢一点。"
        return CopyResult(
            title=title[:28],
            subtitle=subtitle[:24],
            description=description,
            cover_text=cover_text,
            cover_keywords=keywords,
            intro_line=intro,
            outro_line=outro,
        )


class ExternalJsonCopyProvider(CopyProvider):
    """Small replaceable provider for teams that expose their own LLM HTTP endpoint.

    Expected response JSON can either be the CopyResult object directly or an
    object containing a "data" field with that shape.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(
        self,
        book_title: str,
        cleaned_text: str,
        style: str,
        cover_theme: str,
    ) -> CopyResult:
        if not self.settings.llm_api_url:
            raise RuntimeError("LLM_API_URL is not configured. Use mock_llm or configure an external LLM endpoint.")

        payload: dict[str, Any] = {
            "task": "reading_copy",
            "book_title": book_title,
            "style": style,
            "cover_theme": cover_theme,
            "cleaned_text_excerpt": cleaned_text[:1800],
            "requirements": {
                "do_not_rewrite_body": True,
                "tone": "温柔、安静、克制、有陪伴感",
                "output_schema": list(CopyResult.model_fields.keys()) if hasattr(CopyResult, "model_fields") else [],
            },
        }
        headers = {"Content-Type": "application/json"}
        if self.settings.llm_api_key:
            headers["Authorization"] = f"Bearer {self.settings.llm_api_key}"

        with httpx.Client(timeout=45) as client:
            response = client.post(self.settings.llm_api_url, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()

        data = body.get("data", body)
        if isinstance(data, str):
            data = json.loads(data)
        return CopyResult(**data)


class CopyGenerator:
    def __init__(self, settings: Settings, use_mock: bool | None = None) -> None:
        self.settings = settings
        self.use_mock = settings.use_mock_llm if use_mock is None else use_mock
        self.provider: CopyProvider = MockCopyProvider() if self.use_mock else ExternalJsonCopyProvider(settings)

    def generate(
        self,
        book_title: str,
        cleaned_text: str,
        style: str = "",
        cover_theme: str = "",
    ) -> CopyResult:
        return self.provider.generate(book_title, cleaned_text, style, cover_theme)

