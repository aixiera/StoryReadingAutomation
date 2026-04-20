from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.schemas import AudioSegmentInfo, TTSChunk


class Manifest(BaseModel):
    job_id: str
    created_at: str
    book_title: str = ""
    style: str = ""
    cover_theme: str = ""
    input_text_path: str
    cleaned_text_path: str
    title: str
    subtitle: str = ""
    description: str
    cover_text: str
    narration_text_path: str
    chunks: list[TTSChunk] = Field(default_factory=list)
    audio_segments: list[AudioSegmentInfo] = Field(default_factory=list)
    final_audio_path: str
    subtitle_path: str
    cover_image_path: str
    exported_audio_path: str = ""
    exported_cover_image_path: str = ""
    manifest_path: str = ""
    status: str
