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


def test_streaming_uses_short_first_segment_and_larger_following_segments():
    text = (
        "第一部分用于尽快生成首批音频，同时尽量保留自然停顿。"
        "第二部分继续说明后续内容会使用更大的分段长度，以减少上游调用次数。"
        "第三部分补充足够多的文本，验证所有内容都能够按顺序保留下来。"
    ) * 5

    segments = SpeechTextSegmenter().split_for_streaming(
        text,
        first_max_chars=120,
        following_max_chars=400,
    )

    assert "".join(segments) == text
    assert len(segments[0]) <= 120
    assert all(len(segment) <= 400 for segment in segments[1:])
    assert len(segments) >= 2


def test_streaming_segment_limits_must_be_positive():
    segmenter = SpeechTextSegmenter()

    try:
        segmenter.split_for_streaming(
            "测试文本",
            first_max_chars=0,
            following_max_chars=400,
        )
    except ValueError as error:
        assert str(error) == "segment limits must be positive"
    else:
        raise AssertionError("zero first segment limit should be rejected")
