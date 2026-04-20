from __future__ import annotations

import shutil
from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.utils import make_job_id, path_to_str, utc_now_iso, write_text
from app.models.manifest import Manifest
from app.models.schemas import GenerateRequest, GenerateResponse
from app.services.audio_concat import concatenate_audio
from app.services.copy_generator import CopyGenerator
from app.services.cover_composer import compose_cover
from app.services.elevenlabs_client import ElevenLabsClient
from app.services.manifest_builder import save_manifest
from app.services.narration_builder import build_narration_text
from app.services.subtitle_builder import build_srt
from app.services.text_cleaner import clean_text
from app.services.tts_splitter import split_text_to_chunks


logger = get_logger(__name__)


def _export_media_outputs(
    settings: Settings,
    job_id: str,
    final_audio_path: Path,
    cover_path: Path,
) -> tuple[str, str]:
    if settings.media_export_dir is None:
        return "", ""

    export_dir = settings.media_export_dir / job_id
    export_dir.mkdir(parents=True, exist_ok=True)
    exported_audio = export_dir / final_audio_path.name
    exported_cover = export_dir / cover_path.name
    shutil.copy2(final_audio_path, exported_audio)
    shutil.copy2(cover_path, exported_cover)

    wav_sibling = final_audio_path.with_suffix(".wav")
    if wav_sibling.exists():
        shutil.copy2(wav_sibling, export_dir / wav_sibling.name)

    return path_to_str(exported_audio), path_to_str(exported_cover)


def run_generation(request: GenerateRequest, settings: Settings | None = None) -> Manifest:
    settings = settings or get_settings()
    settings.ensure_directories()

    job_id = make_job_id()
    job_dir = settings.jobs_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    book_title = (request.book_title or "").strip()
    style = (request.style or "").strip()
    cover_theme = (request.cover_theme or "").strip()
    use_mock_llm = settings.use_mock_llm if request.use_mock_llm is None else request.use_mock_llm
    use_mock_tts = settings.use_mock_tts if request.use_mock_tts is None else request.use_mock_tts

    logger.info("Starting generation job_id=%s mock_llm=%s mock_tts=%s", job_id, use_mock_llm, use_mock_tts)

    input_text_path = settings.text_dir / f"{job_id}_input.txt"
    cleaned_text_path = settings.text_dir / f"{job_id}_cleaned.txt"
    narration_text_path = settings.text_dir / f"{job_id}_narration.txt"

    write_text(input_text_path, request.text)
    cleaned_text = clean_text(request.text)
    write_text(cleaned_text_path, cleaned_text)

    copy = CopyGenerator(settings, use_mock=use_mock_llm).generate(
        book_title=book_title,
        cleaned_text=cleaned_text,
        style=style,
        cover_theme=cover_theme,
    )
    narration_text = build_narration_text(
        book_title=book_title,
        cleaned_text=cleaned_text,
        intro_line=copy.intro_line,
        outro_line=copy.outro_line,
    )
    write_text(narration_text_path, narration_text)

    chunks = split_text_to_chunks(
        narration_text,
        target_min_seconds=settings.tts_target_min_seconds,
        target_max_seconds=settings.tts_target_max_seconds,
        chars_per_minute=settings.tts_chars_per_minute,
    )
    if not chunks:
        raise RuntimeError("No TTS chunks were produced. Please provide non-empty text.")

    segment_dir = settings.audio_segments_dir / job_id
    audio_segments = ElevenLabsClient(settings, use_mock=use_mock_tts).generate_segments(chunks, segment_dir)

    final_audio_dir = settings.audio_final_dir / job_id
    final_audio_path = final_audio_dir / "final_audio.mp3"
    concatenate_audio(
        [Path(segment.path) for segment in audio_segments],
        final_audio_path,
        settings=settings,
        pause_ms=settings.tts_pause_ms,
    )

    subtitle_path = settings.subtitles_dir / job_id / "subtitles.srt"
    build_srt(chunks, subtitle_path, pause_ms=settings.tts_pause_ms)

    cover_path = settings.cover_dir / job_id / "final_cover.png"
    compose_cover(copy, cover_path, settings=settings, cover_theme=cover_theme)
    exported_audio_path, exported_cover_path = _export_media_outputs(
        settings=settings,
        job_id=job_id,
        final_audio_path=final_audio_path,
        cover_path=cover_path,
    )

    manifest_path = job_dir / "manifest.json"
    manifest = Manifest(
        job_id=job_id,
        created_at=utc_now_iso(),
        book_title=book_title,
        style=style,
        cover_theme=cover_theme,
        input_text_path=path_to_str(input_text_path),
        cleaned_text_path=path_to_str(cleaned_text_path),
        title=copy.title,
        subtitle=copy.subtitle,
        description=copy.description,
        cover_text=copy.cover_text,
        narration_text_path=path_to_str(narration_text_path),
        chunks=chunks,
        audio_segments=audio_segments,
        final_audio_path=path_to_str(final_audio_path),
        subtitle_path=path_to_str(subtitle_path),
        cover_image_path=path_to_str(cover_path),
        exported_audio_path=exported_audio_path,
        exported_cover_image_path=exported_cover_path,
        manifest_path=path_to_str(manifest_path),
        status="completed",
    )
    save_manifest(manifest, manifest_path)
    logger.info("Generation completed job_id=%s", job_id)
    return manifest


def manifest_to_response(manifest: Manifest) -> GenerateResponse:
    return GenerateResponse(
        job_id=manifest.job_id,
        title=manifest.title,
        description=manifest.description,
        final_audio_path=manifest.final_audio_path,
        cover_image_path=manifest.cover_image_path,
        subtitle_path=manifest.subtitle_path,
        manifest_path=manifest.manifest_path,
        status=manifest.status,
        exported_audio_path=manifest.exported_audio_path,
        exported_cover_image_path=manifest.exported_cover_image_path,
    )
