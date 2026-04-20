from app.services.tts_splitter import estimate_duration_sec, split_text_to_chunks


def test_estimate_duration_is_positive():
    assert estimate_duration_sec("这是一句话。") > 0


def test_split_text_to_chunks_respects_sentence_boundaries():
    text = "这是第一句话。" * 80 + "这是最后一句话。"
    chunks = split_text_to_chunks(text, target_min_seconds=4, target_max_seconds=6, chars_per_minute=240)

    assert len(chunks) > 1
    assert all(chunk.index >= 1 for chunk in chunks)
    assert all(chunk.text.endswith("。") for chunk in chunks[:-1])


def test_long_sentence_can_split_by_commas():
    text = "这是一个很长的句子，" * 80 + "终于结束。"
    chunks = split_text_to_chunks(text, target_min_seconds=4, target_max_seconds=6, chars_per_minute=240)

    assert len(chunks) > 1
    assert all(chunk.text for chunk in chunks)

