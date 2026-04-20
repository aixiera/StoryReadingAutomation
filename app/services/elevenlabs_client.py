from __future__ import annotations

import wave
from pathlib import Path

import httpx

from app.core.config import Settings
from app.models.schemas import AudioSegmentInfo, TTSChunk


def _write_silent_wav(path: Path, duration_sec: float, sample_rate: int, channels: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = max(1, int(duration_sec * sample_rate))
    sample_width = 2
    silence_frame = b"\x00" * sample_width * channels
    chunk = silence_frame * min(frame_count, sample_rate)
    remaining = frame_count

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(sample_width)
        wav.setframerate(sample_rate)
        while remaining > 0:
            frames = min(remaining, sample_rate)
            wav.writeframes(chunk[: frames * sample_width * channels])
            remaining -= frames


class ElevenLabsClient:
    def __init__(self, settings: Settings, use_mock: bool | None = None) -> None:
        self.settings = settings
        self.use_mock = settings.use_mock_tts if use_mock is None else use_mock

    def generate_segments(self, chunks: list[TTSChunk], output_dir: Path) -> list[AudioSegmentInfo]:
        output_dir.mkdir(parents=True, exist_ok=True)
        segments: list[AudioSegmentInfo] = []
        for chunk in chunks:
            segment_path = self.generate_segment(chunk, output_dir)
            segments.append(
                AudioSegmentInfo(
                    index=chunk.index,
                    path=str(segment_path.resolve()),
                    duration_sec=chunk.estimated_duration_sec,
                    text=chunk.text,
                )
            )
        return segments

    def generate_segment(self, chunk: TTSChunk, output_dir: Path) -> Path:
        if self.use_mock:
            path = output_dir / f"segment_{chunk.index:03d}.wav"
            _write_silent_wav(
                path=path,
                duration_sec=chunk.estimated_duration_sec,
                sample_rate=self.settings.audio_sample_rate,
                channels=self.settings.audio_channels,
            )
            return path

        return self._generate_real_segment(chunk, output_dir)

    def _generate_real_segment(self, chunk: TTSChunk, output_dir: Path) -> Path:
        if not self.settings.elevenlabs_api_key:
            raise RuntimeError("ELEVENLABS_API_KEY is required when use_mock_tts=false.")
        if not self.settings.elevenlabs_voice_id:
            raise RuntimeError("ELEVENLABS_VOICE_ID is required when use_mock_tts=false.")

        url = (
            "https://api.elevenlabs.io/v1/text-to-speech/"
            f"{self.settings.elevenlabs_voice_id}"
        )
        params = {"output_format": self.settings.elevenlabs_output_format}
        headers = {
            "xi-api-key": self.settings.elevenlabs_api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": chunk.text,
            "model_id": self.settings.elevenlabs_model_id,
            "voice_settings": {
                "stability": 0.55,
                "similarity_boost": 0.75,
                "style": 0.15,
                "use_speaker_boost": True,
            },
        }

        with httpx.Client(timeout=120) as client:
            response = client.post(url, params=params, headers=headers, json=payload)

        if response.status_code >= 400:
            detail = response.text[:500]
            raise RuntimeError(f"ElevenLabs TTS failed: HTTP {response.status_code}: {detail}")

        path = output_dir / f"segment_{chunk.index:03d}.mp3"
        path.write_bytes(response.content)
        return path

