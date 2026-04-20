from __future__ import annotations

import re
from pathlib import Path

from app.models.schemas import TTSChunk


def _format_srt_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _wrap_subtitle(text: str, width: int = 24) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= width:
        return compact
    lines = [compact[index : index + width] for index in range(0, len(compact), width)]
    return "\n".join(lines[:4])


def build_srt(chunks: list[TTSChunk], output_path: Path, pause_ms: int = 180) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    current = 0.0
    blocks: list[str] = []
    pause_seconds = pause_ms / 1000

    for chunk in chunks:
        start = current
        end = start + max(chunk.estimated_duration_sec, 1.0)
        blocks.append(
            "\n".join(
                [
                    str(chunk.index),
                    f"{_format_srt_time(start)} --> {_format_srt_time(end)}",
                    _wrap_subtitle(chunk.text),
                ]
            )
        )
        current = end + pause_seconds

    output_path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    return output_path

