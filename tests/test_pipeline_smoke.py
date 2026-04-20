from pathlib import Path

from app.core.config import Settings
from app.models.schemas import GenerateRequest
from app.services.pipeline import run_generation


def test_pipeline_smoke_with_mock_modes(tmp_path: Path):
    settings = Settings(base_dir=tmp_path)
    settings.media_export_dir = None
    settings.ensure_directories()
    request = GenerateRequest(
        book_title="测试之书",
        text="这是第一段正文。它应该被保留下来。今晚我们只安静地读完这一小段。",
        style="温柔陪伴",
        cover_theme="绿色治愈",
        use_mock_llm=True,
        use_mock_tts=True,
    )

    manifest = run_generation(request, settings=settings)

    assert manifest.status == "completed"
    assert Path(manifest.manifest_path).exists()
    assert Path(manifest.cover_image_path).exists()
    assert Path(manifest.final_audio_path).exists()
    assert Path(manifest.subtitle_path).exists()
    assert Path(manifest.narration_text_path).read_text(encoding="utf-8")
