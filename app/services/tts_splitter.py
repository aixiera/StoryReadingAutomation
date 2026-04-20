from __future__ import annotations

import math
import re

from app.models.schemas import TTSChunk


SENTENCE_RE = re.compile(r".+?(?:[。！？!?；;]+[\"'”’）)]*|$)", re.S)
SOFT_SPLIT_RE = re.compile(r".+?(?:[，,、：:]+|$)", re.S)


def estimate_duration_sec(text: str, chars_per_minute: int = 240) -> float:
    compact = re.sub(r"\s+", "", text)
    cjk_count = len(re.findall(r"[\u3400-\u9fff]", compact))
    other_count = max(0, len(compact) - cjk_count)
    weighted_chars = cjk_count + other_count * 0.55
    seconds = (weighted_chars / max(chars_per_minute, 1)) * 60
    return round(max(seconds, 1.0), 2)


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    sentences = [match.group(0).strip() for match in SENTENCE_RE.finditer(normalized)]
    return [sentence for sentence in sentences if sentence]


def _split_by_soft_punctuation(sentence: str, max_chars: int) -> list[str]:
    if len(sentence) <= max_chars:
        return [sentence]

    pieces = [match.group(0).strip() for match in SOFT_SPLIT_RE.finditer(sentence) if match.group(0).strip()]
    result: list[str] = []
    current = ""
    for piece in pieces:
        if not current:
            current = piece
            continue
        if len(current) + len(piece) <= max_chars:
            current += piece
        else:
            result.append(current)
            current = piece
    if current:
        result.append(current)

    safe: list[str] = []
    for piece in result:
        if len(piece) <= max_chars * 1.25:
            safe.append(piece)
        else:
            for start in range(0, len(piece), max_chars):
                safe.append(piece[start : start + max_chars])
    return safe


def split_text_to_chunks(
    text: str,
    target_min_seconds: int = 40,
    target_max_seconds: int = 55,
    chars_per_minute: int = 240,
) -> list[TTSChunk]:
    if not text.strip():
        return []

    max_chars = max(30, math.floor(target_max_seconds * chars_per_minute / 60))
    sentence_units: list[str] = []
    for sentence in split_sentences(text):
        if estimate_duration_sec(sentence, chars_per_minute) > target_max_seconds:
            sentence_units.extend(_split_by_soft_punctuation(sentence, max_chars))
        else:
            sentence_units.append(sentence)

    chunks: list[str] = []
    current_parts: list[str] = []
    current_duration = 0.0

    for unit in sentence_units:
        unit_duration = estimate_duration_sec(unit, chars_per_minute)
        if not current_parts:
            current_parts.append(unit)
            current_duration = unit_duration
            continue

        would_duration = current_duration + unit_duration
        should_flush = (
            current_duration >= target_min_seconds and would_duration > target_max_seconds
        ) or (
            current_duration >= target_min_seconds * 0.75 and would_duration > target_max_seconds * 1.1
        )

        if should_flush:
            chunks.append("".join(current_parts))
            current_parts = [unit]
            current_duration = unit_duration
        else:
            current_parts.append(unit)
            current_duration = would_duration

    if current_parts:
        chunks.append("".join(current_parts))

    return [
        TTSChunk(
            index=index,
            text=chunk,
            estimated_duration_sec=estimate_duration_sec(chunk, chars_per_minute),
        )
        for index, chunk in enumerate(chunks, start=1)
    ]

