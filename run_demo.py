from __future__ import annotations

import json

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.utils import to_jsonable
from app.models.schemas import GenerateRequest
from app.services.pipeline import manifest_to_response, run_generation


DEMO_TEXT = """
有时候，真正让人疲惫的，并不是事情本身，而是心里反复响起的声音。
它催促你快一点，再快一点；也提醒你不要犯错，不要落后。
可是生活并不总是需要立刻回答。你可以先把呼吸放慢，把注意力放回眼前这一页。
当一个人愿意安静下来，很多答案并不会马上出现，但心会先松开一点。
今晚就读到这里，让文字陪你慢慢落地。
"""


def main() -> None:
    setup_logging()
    request = GenerateRequest(
        book_title="如何停止胡思乱想",
        text=DEMO_TEXT,
        style="治愈安静",
        cover_theme="绿色治愈",
        use_mock_llm=True,
        use_mock_tts=True,
    )
    manifest = run_generation(request, settings=get_settings())
    response = manifest_to_response(manifest)
    print(json.dumps(to_jsonable(response), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

