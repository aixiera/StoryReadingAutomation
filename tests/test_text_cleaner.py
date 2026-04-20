from app.services.text_cleaner import clean_text


def test_clean_text_removes_blank_lines_and_normalizes_punctuation():
    raw = "这是第一行,\n接着是不自然断行。\n\n\n第二段  有   多余空格!"
    cleaned = clean_text(raw)

    assert "\n\n\n" not in cleaned
    assert "这是第一行，接着是不自然断行。" in cleaned
    assert "第二段 有 多余空格！" in cleaned


def test_clean_text_removes_obvious_garbled_replacement_chars():
    cleaned = clean_text("前文\ufffd\ufffd\n后文")

    assert "\ufffd" not in cleaned
    assert "前文后文" in cleaned

