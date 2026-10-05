"""Property and example tests for the pure prose-analysis functions (Rule 28 core)."""

from __future__ import annotations

import prose
from hypothesis import given
from hypothesis import strategies as st

# Sentence bodies: printable text with no terminator characters and no leading/trailing space.
_sentence_bodies = st.text(
    alphabet=st.characters(blacklist_characters=".!?。！？`\n", blacklist_categories=("Cs",)),
    min_size=1,
).map(str.strip).filter(bool)


class TestSplitSentences:
    def test_english_terminators(self):
        assert prose.split_sentences("Hello there. How are you? Fine!") == [
            "Hello there.",
            "How are you?",
            "Fine!",
        ]

    def test_cjk_terminators_need_no_space(self):
        assert prose.split_sentences("今天天氣很好。我們去公園！") == ["今天天氣很好。", "我們去公園！"]

    def test_trailing_fragment_without_terminator_is_a_sentence(self):
        assert prose.split_sentences("One. Two") == ["One.", "Two"]

    def test_dot_inside_a_token_does_not_split(self):
        assert prose.split_sentences("Run skill-lint.py now. Done.") == [
            "Run skill-lint.py now.",
            "Done.",
        ]

    @given(st.lists(_sentence_bodies, min_size=1, max_size=8))
    def test_count_matches_number_of_joined_bodies(self, bodies):
        text = " ".join(b + "." for b in bodies)
        assert len(prose.split_sentences(text)) == len(bodies)

    @given(st.lists(_sentence_bodies, min_size=1, max_size=8))
    def test_no_characters_lost(self, bodies):
        text = "".join(b + "。" for b in bodies)
        assert "".join(prose.split_sentences(text)) == text


_DOC = """\
# Title

[![CI](https://x/badge.svg)](https://x)
![License](https://x/l.svg)

First prose paragraph
spans two lines.

## Install

```bash
echo "Not prose. Not prose. Not prose."
```

- a bullet. with dots.
* another bullet

| a | b |
|---|---|

<!-- comment. -->

Second prose paragraph.
"""


class TestParagraphs:
    def test_only_prose_runs_survive_with_first_line_numbers(self):
        assert prose.paragraphs(_DOC) == [
            prose.Paragraph(line=6, text="First prose paragraph spans two lines."),
            prose.Paragraph(line=23, text="Second prose paragraph."),
        ]

    def test_empty_document_has_no_paragraphs(self):
        assert prose.paragraphs("") == []

    @given(st.lists(_sentence_bodies, min_size=1, max_size=6))
    def test_fenced_code_never_leaks_into_prose(self, bodies):
        code = "\n".join(bodies)
        doc = f"Intro.\n\n```\n{code}\n```\n\nOutro.\n"
        assert [p.text for p in prose.paragraphs(doc)] == ["Intro.", "Outro."]


class TestSentenceTooLong:
    def test_english_limit_is_35_words(self):
        assert not prose.sentence_too_long(" ".join(["w"] * 35) + ".")
        assert prose.sentence_too_long(" ".join(["w"] * 36) + ".")

    def test_cjk_limit_is_80_chars(self):
        assert not prose.sentence_too_long("字" * 80 + "。")
        assert prose.sentence_too_long("字" * 81 + "。")

    def test_short_cjk_with_long_english_term_is_fine(self):
        assert not prose.sentence_too_long("執行 `uv run skill-lint.py check .` 即可。")

    def test_bilingual_sentence_judged_by_cjk_count_not_total_length(self):
        mixed = "這是一句短中文 " + " ".join(["word"] * 20) + " 結尾。"
        assert not prose.sentence_too_long(mixed)
        assert prose.sentence_too_long("字" * 81 + " with spaces 。")

    @given(st.integers(min_value=1, max_value=200))
    def test_english_monotone_in_word_count(self, n):
        assert prose.sentence_too_long(" ".join(["w"] * n)) == (n > 35)


class TestFindPhrases:
    def test_whole_word_case_insensitive_with_paragraph_line(self):
        doc = "# T\n\nA Powerful, blazing-fast tool.\n\nPowerfully unrelated.\n"
        assert prose.find_phrases(doc, ["powerful", "blazing"]) == [
            (3, "powerful"),
            (3, "blazing"),
        ]

    def test_code_blocks_are_ignored(self):
        doc = "```\npowerful\n```\n"
        assert prose.find_phrases(doc, ["powerful"]) == []

    def test_inline_code_spans_are_ignored(self):
        assert prose.find_phrases("Pass the `--powerful` flag.\n", ["powerful"]) == []

    def test_multiword_phrase(self):
        assert prose.find_phrases("It is best-in-class.\n", ["best-in-class"]) == [
            (1, "best-in-class")
        ]

    @given(st.from_regex(r"\A[a-z]{3,10}\Z"), _sentence_bodies.filter(lambda s: s[0].isalpha()))
    def test_listed_word_is_always_found_and_unlisted_never(self, word, filler):
        doc = f"{filler} {word} {filler}."
        assert [w for _, w in prose.find_phrases(doc, [word])] == [word]
        assert prose.find_phrases(doc, [word + "zz"]) == []


class TestLead:
    def test_lead_within_eight_nonblank_lines_after_h1(self):
        doc = "# T\n\n![b](x)\n![b](x)\n\nDoes one thing well.\n"
        assert prose.lead_issues(doc) == []

    def test_lead_buried_below_eight_nonblank_lines(self):
        doc = "# T\n" + "![b](x)\n" * 9 + "\nDoes one thing well.\n"
        assert prose.lead_issues(doc) == [prose.LeadStatus.BURIED]

    def test_no_prose_at_all(self):
        assert prose.lead_issues("# T\n\n- only bullets\n") == [prose.LeadStatus.MISSING]

    def test_throat_clearing_opener(self):
        doc = "# T\n\nWelcome to the repository for T.\n"
        assert prose.lead_issues(doc) == [prose.LeadStatus.THROAT_CLEARING]

    def test_throat_clearing_variants(self):
        for opener in ("This repository contains", "This project is"):
            assert prose.lead_issues(f"# T\n\n{opener} things.\n") == [prose.LeadStatus.THROAT_CLEARING]

    def test_buried_and_throat_clearing_both_reported(self):
        doc = "# T\n" + "![b](x)\n" * 9 + "\nWelcome to T.\n"
        assert prose.lead_issues(doc) == [prose.LeadStatus.BURIED, prose.LeadStatus.THROAT_CLEARING]


class TestEmDashHeavy:
    def test_two_is_fine_three_is_heavy(self):
        assert not prose.em_dash_heavy("a — b — c")
        assert prose.em_dash_heavy("a — b — c — d")


class TestBlockquotes:
    def test_blockquote_marker_is_stripped_and_text_kept_as_prose(self):
        doc = "# T\n\nIntro.\n\n> Quoted line one\n> continues here.\n"
        assert prose.paragraphs(doc)[1] == prose.Paragraph(line=5, text="Quoted line one continues here.")

    def test_nested_marker_and_bare_marker_lines(self):
        doc = "> > deep quote.\n>\n> after blank marker.\n"
        assert [p.text for p in prose.paragraphs(doc)] == ["deep quote.", "after blank marker."]

    def test_quoted_code_fence_is_still_code(self):
        doc = "> ```\n> powerful\n> ```\n"
        assert prose.find_phrases(doc, ["powerful"]) == []
