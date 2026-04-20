from __future__ import annotations

import re
import unicodedata


_SENTENCE_END_RE = re.compile(r"[。！？!?；;：:]$|[。！？!?；;：:][\"'”’）)]?$")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_CJK_RE = re.compile(r"[\u3400-\u9fff]")


def _looks_like_heading(line: str) -> bool:
    if len(line) <= 18 and re.match(r"^(第[一二三四五六七八九十百千万\d]+[章节篇部]|[一二三四五六七八九十\d]+[、.．])", line):
        return True
    return False


def _needs_space(left: str, right: str) -> bool:
    if not left or not right:
        return False
    return bool(re.search(r"[A-Za-z0-9]$", left) and re.search(r"^[A-Za-z0-9]", right))


def normalize_punctuation(text: str) -> str:
    replacements = {
        "，": "，",
        "。": "。",
        "！": "！",
        "？": "？",
        "；": "；",
        "：": "：",
        "（": "（",
        "）": "）",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)

    text = re.sub(r"(?<=[\u3400-\u9fff]),(?=($|[\s\"'”’）)]|[\u3400-\u9fff]))", "，", text)
    text = re.sub(r"(?<=[\u3400-\u9fff])\.(?=($|[\s\"'”’）)]|[\u3400-\u9fff]))", "。", text)
    text = re.sub(r"(?<=[\u3400-\u9fff])!(?=($|[\s\"'”’）)]|[\u3400-\u9fff]))", "！", text)
    text = re.sub(r"(?<=[\u3400-\u9fff])\?(?=($|[\s\"'”’）)]|[\u3400-\u9fff]))", "？", text)
    text = re.sub(r"(?<=[\u3400-\u9fff]);(?=($|[\s\"'”’）)]|[\u3400-\u9fff]))", "；", text)
    text = re.sub(r"(?<=[\u3400-\u9fff]):(?=($|[\s\"'”’）)]|[\u3400-\u9fff]))", "：", text)

    text = re.sub(r"[。]{2,}", "。", text)
    text = re.sub(r"[，]{2,}", "，", text)
    text = re.sub(r"[！!]{2,}", "！", text)
    text = re.sub(r"[？?]{2,}", "？", text)
    return text


def clean_text(text: str) -> str:
    """Lightly clean book text without rewriting the body content."""
    if text is None:
        return ""

    text = text.replace("\ufeff", "").replace("\ufffd", "")
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u3000", " ")
    text = _CONTROL_RE.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = normalize_punctuation(text)

    raw_lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in raw_lines if line]
    if not lines:
        return ""

    merged: list[str] = []
    for line in lines:
        if not merged:
            merged.append(line)
            continue

        previous = merged[-1]
        should_merge = (
            not _SENTENCE_END_RE.search(previous)
            and not _looks_like_heading(line)
            and len(previous) < 120
            and len(line) < 120
        )
        if should_merge:
            sep = " " if _needs_space(previous, line) else ""
            merged[-1] = previous + sep + line
        else:
            merged.append(line)

    cleaned = normalize_punctuation("\n".join(merged))
    cleaned = re.sub(r" *([，。！？；：、]) *", r"\1", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = cleaned.strip()

    if not _CJK_RE.search(cleaned):
        cleaned = re.sub(r" +", " ", cleaned)
    return cleaned
