from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    book_title: Optional[str] = Field(default="", description="书名，可选")
    text: str = Field(min_length=1, description="书本文字正文，必填")
    style: Optional[str] = Field(default="", description="风格标签")
    cover_theme: Optional[str] = Field(default="", description="封面氛围")
    use_mock_tts: Optional[bool] = Field(default=None, description="是否强制使用 mock TTS")
    use_mock_llm: Optional[bool] = Field(default=None, description="是否强制使用 mock LLM")


class CopyResult(BaseModel):
    title: str
    subtitle: str = ""
    description: str
    cover_text: str
    cover_keywords: list[str] = Field(default_factory=list)
    intro_line: str
    outro_line: str = ""


class TTSChunk(BaseModel):
    index: int
    text: str
    estimated_duration_sec: float


class AudioSegmentInfo(BaseModel):
    index: int
    path: str
    duration_sec: float
    text: str


class GenerateResponse(BaseModel):
    job_id: str
    title: str
    description: str
    final_audio_path: str
    cover_image_path: str
    subtitle_path: str
    manifest_path: str
    status: str
    exported_audio_path: str = ""
    exported_cover_image_path: str = ""


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "xulan-reading-generator"
