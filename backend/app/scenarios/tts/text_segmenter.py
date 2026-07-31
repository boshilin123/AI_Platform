from __future__ import annotations


class SpeechTextSegmenter:
    """Split multilingual speech text without cutting natural sentence boundaries."""

    STRONG_BOUNDARIES = frozenset("。！？.!?；;\n")
    SOFT_BOUNDARIES = frozenset("，,、：:")

    def split(self, text: str, max_chars: int) -> list[str]:
        return self._split_with_limits(
            text,
            first_max_chars=max_chars,
            following_max_chars=max_chars,
        )

    def split_for_streaming(
        self,
        text: str,
        *,
        first_max_chars: int,
        following_max_chars: int,
    ) -> list[str]:
        """Create a short first segment so upstream audio can start sooner."""
        return self._split_with_limits(
            text,
            first_max_chars=first_max_chars,
            following_max_chars=following_max_chars,
        )

    def _split_with_limits(
        self,
        text: str,
        *,
        first_max_chars: int,
        following_max_chars: int,
    ) -> list[str]:
        normalized = text.strip()
        if not normalized:
            return []
        if first_max_chars < 1 or following_max_chars < 1:
            raise ValueError("segment limits must be positive")

        segments: list[str] = []
        cursor = 0
        text_length = len(normalized)
        while cursor < text_length:
            max_chars = first_max_chars if not segments else following_max_chars
            hard_end = min(cursor + max_chars, text_length)
            if hard_end == text_length:
                segment = normalized[cursor:hard_end].strip()
                if segment:
                    segments.append(segment)
                break

            split_at = self._find_boundary(normalized, cursor, hard_end, max_chars)
            segment = normalized[cursor:split_at].strip()
            if segment:
                segments.append(segment)
            cursor = split_at
            while cursor < text_length and normalized[cursor].isspace():
                cursor += 1
        return segments

    def _find_boundary(self, text: str, start: int, hard_end: int, max_chars: int) -> int:
        minimum = start + max(1, max_chars // 3)
        window = text[start:hard_end]

        for boundaries in (self.STRONG_BOUNDARIES, self.SOFT_BOUNDARIES):
            for index in range(len(window) - 1, minimum - start - 1, -1):
                if window[index] in boundaries:
                    return start + index + 1

        for index in range(len(window) - 1, minimum - start - 1, -1):
            if window[index].isspace():
                return start + index + 1
        return hard_end
