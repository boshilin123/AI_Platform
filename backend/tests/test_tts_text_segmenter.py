from app.scenarios.tts.text_segmenter import SpeechTextSegmenter


def test_segments_chinese_at_sentence_boundaries():
    text = "第一段介绍。第二段包含更多内容！第三段结束。"
    segments = SpeechTextSegmenter().split(text, 12)

    assert "".join(segments) == text
    assert all(len(segment) <= 12 for segment in segments)
    assert segments[0].endswith("。")


def test_segments_english_at_words_and_sentence_boundaries():
    text = (
        "This is the first sentence. "
        "This second sentence explains streaming audio playback in English."
    )
    segments = SpeechTextSegmenter().split(text, 36)

    assert " ".join(segments).split() == text.split()
    assert all(len(segment) <= 36 for segment in segments)
    assert segments[0].endswith(".")


def test_segments_unpunctuated_text_without_losing_characters():
    text = "abcdefghij" * 10
    segments = SpeechTextSegmenter().split(text, 17)

    assert "".join(segments) == text
    assert all(1 <= len(segment) <= 17 for segment in segments)
