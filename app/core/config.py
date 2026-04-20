from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is installed in normal setup
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parents[2]

if load_dotenv is not None:
    load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _resolve_path(base_dir: Path, value: str | None, default: str) -> Path:
    candidate = Path(value or default)
    if candidate.is_absolute():
        return candidate
    return base_dir / candidate


@dataclass
class Settings:
    base_dir: Path = BASE_DIR
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "dev"))
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _env_int("PORT", 8000))

    use_mock_llm: bool = field(default_factory=lambda: _env_bool("USE_MOCK_LLM", True))
    use_mock_tts: bool = field(default_factory=lambda: _env_bool("USE_MOCK_TTS", True))

    elevenlabs_api_key: str = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))
    elevenlabs_voice_id: str = field(default_factory=lambda: os.getenv("ELEVENLABS_VOICE_ID", ""))
    elevenlabs_model_id: str = field(default_factory=lambda: os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"))
    elevenlabs_output_format: str = field(default_factory=lambda: os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128"))

    llm_api_url: str = field(default_factory=lambda: os.getenv("LLM_API_URL", ""))
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", ""))

    tts_target_min_seconds: int = field(default_factory=lambda: _env_int("TTS_TARGET_MIN_SECONDS", 40))
    tts_target_max_seconds: int = field(default_factory=lambda: _env_int("TTS_TARGET_MAX_SECONDS", 55))
    tts_chars_per_minute: int = field(default_factory=lambda: _env_int("TTS_CHARS_PER_MINUTE", 240))
    tts_pause_ms: int = field(default_factory=lambda: _env_int("TTS_PAUSE_MS", 180))

    cover_width: int = field(default_factory=lambda: _env_int("COVER_WIDTH", 1080))
    cover_height: int = field(default_factory=lambda: _env_int("COVER_HEIGHT", 1440))

    audio_sample_rate: int = field(default_factory=lambda: _env_int("AUDIO_SAMPLE_RATE", 44100))
    audio_channels: int = field(default_factory=lambda: _env_int("AUDIO_CHANNELS", 1))

    xulan_asset_path: Path | None = None
    media_export_dir: Path | None = None

    def __post_init__(self) -> None:
        self.base_dir = Path(self.base_dir).resolve()
        self.output_dir = self.base_dir / "output"
        self.jobs_dir = self.output_dir / "jobs"
        self.audio_segments_dir = self.output_dir / "audio_segments"
        self.audio_final_dir = self.output_dir / "audio_final"
        self.subtitles_dir = self.output_dir / "subtitles"
        self.cover_dir = self.output_dir / "cover"
        self.text_dir = self.output_dir / "text"
        self.assets_dir = self.base_dir / "assets"
        self.backgrounds_dir = self.assets_dir / "backgrounds"
        self.fonts_dir = self.assets_dir / "fonts"
        self.placeholders_dir = self.assets_dir / "placeholders"
        if self.xulan_asset_path is None:
            self.xulan_asset_path = _resolve_path(
                self.base_dir,
                os.getenv("XULAN_ASSET_PATH"),
                "assets/xulan/xulan_main.png",
            )
        else:
            self.xulan_asset_path = Path(self.xulan_asset_path)
        if self.media_export_dir is None:
            raw_export_dir = os.getenv("MEDIA_EXPORT_DIR", "").strip()
            if raw_export_dir:
                export_path = Path(raw_export_dir)
                self.media_export_dir = export_path if export_path.is_absolute() else self.base_dir / export_path
            else:
                self.media_export_dir = None
        else:
            self.media_export_dir = Path(self.media_export_dir)

    def ensure_directories(self) -> None:
        for path in (
            self.jobs_dir,
            self.audio_segments_dir,
            self.audio_final_dir,
            self.subtitles_dir,
            self.cover_dir,
            self.text_dir,
            self.assets_dir / "xulan",
            self.backgrounds_dir,
            self.fonts_dir,
            self.placeholders_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)
        if self.media_export_dir is not None:
            self.media_export_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
