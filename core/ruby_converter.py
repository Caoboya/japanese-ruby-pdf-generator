# -*- coding: utf-8 -*-

import html
import re
from pathlib import Path

from fugashi import Tagger
import unidic_lite


dicdir = Path(unidic_lite.DICDIR)
mecabrc = dicdir / "mecabrc"
tagger = Tagger(f'-r "{mecabrc}" -d "{dicdir}"')

KANJI_PATTERN = re.compile(r"[一-龯々〆ヵヶ]")


def contains_kanji(text: str) -> bool:
    return bool(KANJI_PATTERN.search(text))


def kata_to_hira(text: str) -> str:
    if not text:
        return ""

    return "".join(
        chr(ord(ch) - 0x60) if "ァ" <= ch <= "ヴ" else ch
        for ch in text
    )


def safe_get_reading(word) -> str:
    for attr in ("kana", "reading", "pron", "pronBase"):
        try:
            value = getattr(word.feature, attr, None)
            if value and value != "*":
                return str(value)
        except Exception:
            pass

    try:
        feats = list(word.feature)
        for idx in (7, 6, 8, 9):
            if idx < len(feats):
                value = feats[idx]
                if value and value != "*":
                    return str(value)
    except Exception:
        pass

    return ""


def split_common_parts(surface: str, reading: str):
    prefix_len = 0
    max_prefix = min(len(surface), len(reading))

    while prefix_len < max_prefix and surface[prefix_len] == reading[prefix_len]:
        prefix_len += 1

    suffix_len = 0
    max_suffix = min(len(surface) - prefix_len, len(reading) - prefix_len)

    while (
        suffix_len < max_suffix
        and surface[-1 - suffix_len] == reading[-1 - suffix_len]
    ):
        suffix_len += 1

    prefix = surface[:prefix_len]

    if suffix_len > 0:
        middle_surface = surface[prefix_len: len(surface) - suffix_len]
        middle_reading = reading[prefix_len: len(reading) - suffix_len]
        suffix = surface[len(surface) - suffix_len:]
    else:
        middle_surface = surface[prefix_len:]
        middle_reading = reading[prefix_len:]
        suffix = ""

    return prefix, middle_surface, middle_reading, suffix


def build_ruby_html(surface: str, reading_hira: str) -> str:
    if not surface:
        return ""

    if not reading_hira or surface == reading_hira:
        return html.escape(surface)

    prefix, middle_surface, middle_reading, suffix = split_common_parts(
        surface, reading_hira
    )

    if not middle_surface or not middle_reading or not contains_kanji(middle_surface):
        return html.escape(surface)

    return (
        f"{html.escape(prefix)}"
        f"<ruby>{html.escape(middle_surface)}<rt>{html.escape(middle_reading)}</rt></ruby>"
        f"{html.escape(suffix)}"
    )


def to_ruby_html(text: str) -> str:
    if not text.strip():
        return ""

    parts = []

    for word in tagger(text):
        surface = word.surface

        if contains_kanji(surface):
            reading_kata = safe_get_reading(word)
            if reading_kata:
                reading_hira = kata_to_hira(reading_kata)
                parts.append(build_ruby_html(surface, reading_hira))
            else:
                parts.append(html.escape(surface))
        else:
            parts.append(html.escape(surface))

    return "".join(parts)


def text_file_to_paragraphs(txt_path: Path) -> str:
    text = txt_path.read_text(encoding="utf-8")

    paragraphs = []
    for line in text.splitlines():
        if line.strip():
            paragraphs.append(f"<p>{to_ruby_html(line)}</p>")
        else:
            paragraphs.append("<p>&nbsp;</p>")

    return "".join(paragraphs)