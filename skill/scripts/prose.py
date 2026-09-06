"""Pure prose-analysis functions behind Rule 28 (plain prose in human-facing documents).

Stdlib only. Nothing here touches the filesystem or knows about LintResult; rules.py
maps the findings produced by `analyze()` onto lint results.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

# A sentence ends at an ASCII terminator followed by whitespace or end-of-text, or at a
# CJK full-width terminator with no whitespace required. `skill-lint.py now` keeps its dot
# because no whitespace follows it.
_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+|(?<=[。！？])")


def split_sentences(text: str) -> list[str]:
    """Split a paragraph into sentences, keeping terminators, dropping empty pieces."""
    return [s for s in (p.strip() for p in _SENTENCE_END_RE.split(text)) if s]


# ---------------------------------------------------------------------------
# Paragraph extraction
# ---------------------------------------------------------------------------

_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_BADGE_RE = re.compile(r"^\s*(\[!\[|!\[)")
_HEADING_RE = re.compile(r"^\s*#{1,6}\s")
_LIST_ITEM_RE = re.compile(r"^\s*([-*+]|\d+[.)])\s")
_TABLE_RE = re.compile(r"^\s*\|")
_HTML_RE = re.compile(r"^\s*<")
_CJK_RE = re.compile(r"[぀-ヿ㐀-䶿一-鿿豈-﫿]")

_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
_BLOCKQUOTE_RE = re.compile(r"^(\s*>)+\s?")

_NON_PROSE_LINE_RES = (_BADGE_RE, _HEADING_RE, _LIST_ITEM_RE, _TABLE_RE, _HTML_RE)


@dataclass(frozen=True, slots=True)
class Paragraph:
    """A run of prose lines, joined with spaces, tagged with its first 1-based line number."""

    line: int
    text: str


def paragraphs(text: str) -> list[Paragraph]:
    """Return prose paragraphs only: no code, headings, badges, lists, tables, or HTML.

    Blockquote markers are stripped first, so quoted prose counts as prose and a
    quoted code fence still counts as code.
    """
    out: list[Paragraph] = []
    in_fence = False
    current: list[str] = []
    start = 0

    def flush() -> None:
        if current:
            joined = " ".join(_INLINE_CODE_RE.sub("", s).strip() for s in current)
            out.append(Paragraph(start, " ".join(joined.split())))
            current.clear()

    for n, raw in enumerate(text.splitlines(), start=1):
        raw = _BLOCKQUOTE_RE.sub("", raw)  # quoted prose is still prose
        if _FENCE_RE.match(raw):
            in_fence = not in_fence
            flush()
            continue
        if in_fence:
            continue
        if not raw.strip() or any(r.match(raw) for r in _NON_PROSE_LINE_RES):
            flush()
            continue
        if not current:
            start = n
        current.append(raw)
    flush()
    return out


# ---------------------------------------------------------------------------
# Sentence length
# ---------------------------------------------------------------------------

MAX_WORDS = 35
MAX_CJK_CHARS = 80


def sentence_too_long(sentence: str) -> bool:
    """Over 35 whitespace-separated words, or over 80 CJK characters.

    CJK text has no word boundaries, so its characters are counted directly;
    Latin tokens inside a Chinese sentence count as words, not characters, so a
    bilingual sentence is judged by whichever half is actually long.
    """
    if len(sentence.split()) > MAX_WORDS:
        return True
    return len(_CJK_RE.findall(sentence)) > MAX_CJK_CHARS


# ---------------------------------------------------------------------------
# Phrase matching
# ---------------------------------------------------------------------------


def find_phrases(text: str, phrases: list[str]) -> list[tuple[int, str]]:
    """Whole-word, case-insensitive hits in prose paragraphs, tagged with the paragraph's line.

    Hits are ordered by paragraph, then by position in the paragraph, so the
    caller can report them in reading order. Phrases inside code blocks,
    badges, headings, lists, and tables never match because `paragraphs()`
    drops those lines first.
    """
    if not phrases:
        return []
    alternation = "|".join(re.escape(p) for p in sorted(phrases, key=len, reverse=True))
    phrase_re = re.compile(rf"(?<!\w)(?:{alternation})(?!\w)", re.IGNORECASE)
    hits: list[tuple[int, str]] = []
    for para in paragraphs(text):
        for m in phrase_re.finditer(para.text):
            hits.append((para.line, m.group().lower()))
    return hits


# ---------------------------------------------------------------------------
# Lead paragraph
# ---------------------------------------------------------------------------

MAX_LINES_BEFORE_LEAD = 8

_THROAT_CLEARING_RE = re.compile(
    r"^(welcome to|this (repository|repo) contains|this project is)\b", re.IGNORECASE
)


class LeadStatus(Enum):
    MISSING = "missing"
    BURIED = "buried"
    THROAT_CLEARING = "throat_clearing"


def lead_issues(text: str) -> list[LeadStatus]:
    """Judge the first prose paragraph: present, near the top, and not throat-clearing.

    Returns every LeadStatus that applies (BURIED and THROAT_CLEARING can
    co-occur); an empty list means the lead is fine.
    """
    paras = paragraphs(text)
    if not paras:
        return [LeadStatus.MISSING]
    lead = paras[0]
    lines = text.splitlines()
    h1_index = next((i for i, ln in enumerate(lines) if ln.startswith("# ")), -1)
    between = lines[h1_index + 1 : lead.line - 1]
    issues: list[LeadStatus] = []
    if sum(1 for ln in between if ln.strip()) > MAX_LINES_BEFORE_LEAD:
        issues.append(LeadStatus.BURIED)
    if _THROAT_CLEARING_RE.match(lead.text):
        issues.append(LeadStatus.THROAT_CLEARING)
    return issues


# ---------------------------------------------------------------------------
# Em-dash density
# ---------------------------------------------------------------------------

MAX_EM_DASHES_PER_PARAGRAPH = 2


def em_dash_heavy(paragraph_text: str) -> bool:
    """Three or more em-dashes in one paragraph reads as stitched-together prose."""
    return paragraph_text.count("—") > MAX_EM_DASHES_PER_PARAGRAPH


# ---------------------------------------------------------------------------
# Whole-document report
# ---------------------------------------------------------------------------

MARKETING_SUPERLATIVES = [
    "powerful", "blazing", "blazingly", "effortless", "effortlessly", "best-in-class",
    "game-changing", "state-of-the-art", "cutting-edge", "world-class", "next-generation",
    "revolutionary", "lightning-fast", "ultimate", "supercharge", "supercharged",
]

MAX_SENTENCES_PER_PARAGRAPH = 5


@dataclass(frozen=True)
class ProseReport:
    """Everything Rule 28 can say about one human-facing document.

    Line numbers are the first line of the offending paragraph.
    """

    superlatives: list[tuple[int, str]]
    lead: list[LeadStatus]
    lead_text: str
    long_sentences: list[int]
    long_paragraphs: list[int]
    dash_heavy: list[int]


def analyze(text: str) -> ProseReport:
    paras = paragraphs(text)
    long_sentences = [
        p.line for p in paras for s in split_sentences(p.text) if sentence_too_long(s)
    ]
    long_paragraphs = [
        p.line for p in paras if len(split_sentences(p.text)) > MAX_SENTENCES_PER_PARAGRAPH
    ]
    return ProseReport(
        superlatives=find_phrases(text, MARKETING_SUPERLATIVES),
        lead=lead_issues(text),
        lead_text=paras[0].text[:40] if paras else "",
        long_sentences=long_sentences,
        long_paragraphs=long_paragraphs,
        dash_heavy=[p.line for p in paras if em_dash_heavy(p.text)],
    )
