from __future__ import annotations

import shutil
import wave
from pathlib import Path

from app.core.config import Settings


def _concat_with_pydub(segment_paths: list[Path], output_path: Path, settings: Settings, pause_ms: int) -> None:
    try:
        from pydub import AudioSegment, effects
    except ImportError as exc:  # pragma: no cover - exercised only without deps
        raise RuntimeError("pydub is not installed. Run pip install -r requirements.txt.") from exc

    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=pause_ms, frame_rate=settings.audio_sample_rate)

    for index, path in enumerate(segment_paths):
        segment = AudioSegment.from_file(path)
        segment = segment.set_frame_rate(settings.audio_sample_rate)
        segment = segment.set_channels(settings.audio_channels)
        segment = segment.set_sample_width(2)
        if segment.rms > 0:
            segment = effects.normalize(segment)
        combined += segment
        if index < len(segment_paths) - 1:
            combined += pause

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.export(output_path, format="mp3", bitrate="128k")


def _validate_wav(path: Path) -> tuple[int, int, int]:
    with wave.open(str(path), "rb") as wav:
        return wav.getframerate(), wav.getnchannels(), wav.getsampwidth()


def _concat_wav_fallback(segment_paths: list[Path], output_path: Path, pause_ms: int) -> None:
    if not segment_paths:
        raise RuntimeError("No audio segments were provided for concatenation.")

    params = _validate_wav(segment_paths[0])
    frame_rate, channels, sample_width = params
    for path in segment_paths[1:]:
        if _validate_wav(path) != params:
            raise RuntimeError("WAV fallback can only concatenate segments with the same format.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pause_frames = int(frame_rate * pause_ms / 1000)
    silence = b"\x00" * pause_frames * channels * sample_width

    with wave.open(str(output_path), "wb") as out:
        out.setframerate(frame_rate)
        out.setnchannels(channels)
        out.setsampwidth(sample_width)
        for index, path in enumerate(segment_paths):
            with wave.open(str(path), "rb") as wav:
                out.writeframes(wav.readframes(wav.getnframes()))
            if index < len(segment_paths) - 1:
                out.writeframes(silence)

    wav_sibling = output_path.with_suffix(".wav")
    if wav_sibling != output_path:
        shutil.copyfile(output_path, wav_sibling)


def concatenate_audio(
    segment_paths: list[Path],
    output_path: Path,
    settings: Settings,
    pause_ms: int | None = None,
) -> Path:
    """Normalize and concatenate audio segments.

    In normal use this exports a real MP3 through pydub/ffmpeg. In pure mock
    mode, if ffmpeg is missing, it falls back to writing WAV audio bytes to the
    requested path and also creates a .wav sibling for direct playback.
    """
    pause = settings.tts_pause_ms if pause_ms is None else pause_ms
    segment_paths = [Path(path) for path in segment_paths]
    if not segment_paths:
        raise RuntimeError("No audio segments were provided for concatenation.")

    all_wav = all(path.suffix.lower() == ".wav" for path in segment_paths)

    if shutil.which("ffmpeg"):
        try:
            _concat_with_pydub(segment_paths, output_path, settings, pause)
            return output_path
        except Exception as exc:
            if all_wav:
                _concat_wav_fallback(segment_paths, output_path, pause)
                return output_path
            raise RuntimeError(f"Audio concatenation failed. Check ffmpeg and input audio files: {exc}") from exc

    if all_wav:
        _concat_wav_fallback(segment_paths, output_path, pause)
        return output_path

    raise RuntimeError(
        "ffmpeg was not found. Install ffmpeg to concatenate real MP3 segments, "
        "or run with mock_tts=true to use the WAV fallback."
    )
