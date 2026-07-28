from __future__ import annotations


class SpeechTextSegmenter:
    """Split multilingual speech text without cutting natural sentence boundaries."""

    STRONG_BOUNDARIES = frozenset("。！？.!?；;\n")
    SOFT_BOUNDARIES = frozenset("，,、：:")

    def split(self, text: str, max_chars: int) -> list[str]:
        normalized = text.strip()
        if not normalized:
            return []
        if max_chars < 1:
            raise ValueError("max_chars must be positive")

        segments: list[str] = []
        cursor = 0
        text_length = len(normalized)
        while cursor < text_length:
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
