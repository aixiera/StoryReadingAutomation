from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.utils import to_jsonable
from app.models.schemas import GenerateRequest
from app.services.pipeline import manifest_to_response, run_generation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="序蓝酱读书内容生成器 CLI")
    parser.add_argument("--book-title", default="", help="书名，可选")
    parser.add_argument("--text-file", help="正文文本文件路径")
    parser.add_argument("--text", help="直接传入正文文本")
    parser.add_argument("--style", default="", help="风格标签，例如：治愈安静")
    parser.add_argument("--cover-theme", default="", help="封面氛围，例如：绿色治愈")
    parser.add_argument("--mock-llm", action="store_true", help="强制使用 mock LLM")
    parser.add_argument("--real-llm", action="store_true", help="强制使用外部 LLM endpoint")
    parser.add_argument("--mock-tts", action="store_true", help="强制使用 mock TTS")
    parser.add_argument("--real-tts", action="store_true", help="强制使用真实 ElevenLabs TTS")
    return parser.parse_args()


def _resolve_mock_flag(mock_flag: bool, real_flag: bool) -> bool | None:
    if mock_flag and real_flag:
        raise SystemExit("Do not pass both mock and real flags for the same provider.")
    if mock_flag:
        return True
    if real_flag:
        return False
    return None


def main() -> None:
    setup_logging()
    args = parse_args()

    if args.text_file:
        text = Path(args.text_file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        raise SystemExit("Please provide --text-file or --text.")

    request = GenerateRequest(
        book_title=args.book_title,
        text=text,
        style=args.style,
        cover_theme=args.cover_theme,
        use_mock_llm=_resolve_mock_flag(args.mock_llm, args.real_llm),
        use_mock_tts=_resolve_mock_flag(args.mock_tts, args.real_tts),
    )
    manifest = run_generation(request, settings=get_settings())
    response = manifest_to_response(manifest)
    print(json.dumps(to_jsonable(response), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

