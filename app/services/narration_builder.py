from __future__ import annotations


def build_narration_text(
    book_title: str,
    cleaned_text: str,
    intro_line: str = "",
    outro_line: str = "",
) -> str:
    if not intro_line:
        if book_title:
            intro_line = f"晚上好，这里是序蓝酱。今天陪你读一段《{book_title}》。"
        else:
            intro_line = "晚上好，这里是序蓝酱。今天陪你读一段安静的文字。"

    parts = [intro_line.strip(), cleaned_text.strip()]
    if outro_line:
        parts.append(outro_line.strip())
    return "\n\n".join(part for part in parts if part)

