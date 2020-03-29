import re
import typing as T

import pytest

from bubblesub.fmt.ass.event import AssEvent

from .process import (
    ProcessingError,
    convert_to_smart_quotes,
    fix_bad_dialogue_dashes,
    fix_dangling_ass_tags,
    fix_disjoint_ass_tags,
    fix_punctuation,
    fix_useless_ass_tags,
    fix_whitespace,
)


def test_fix_disjointed_ass_tags() -> None:
    assert fix_disjoint_ass_tags("{asd}{asd}") == "{asdasd}"


def test_fix_dangling_ass_tags() -> None:
    assert fix_dangling_ass_tags("{\\i1}asd{\\i0}") == "{\\i1}asd"


def test_fix_bad_dialogue_dashes() -> None:
    assert (
        fix_bad_dialogue_dashes("- asd\n- asd")
        == "\N{EN DASH} asd\n\N{EN DASH} asd"
    )
    assert (
        fix_bad_dialogue_dashes("{\\nonsense- asd\n- asd")
        == "{\\nonsense- asd\n\N{EN DASH} asd"
    )
    assert (
        fix_bad_dialogue_dashes("{\\i1}- asd\n- asd")
        == "{\\i1}\N{EN DASH} asd\n\N{EN DASH} asd"
    )
    assert (
        fix_bad_dialogue_dashes("- asd\n{\\i1}- asd")
        == "\N{EN DASH} asd\n{\\i1}\N{EN DASH} asd"
    )


def test_fix_whitespace() -> None:
    assert fix_whitespace(" asd ") == "asd"
    assert fix_whitespace("asd \nasd") == "asd\nasd"
    assert fix_whitespace("asd\n asd") == "asd\nasd"
    assert fix_whitespace("asd  \n  asd  \n  asd\n") == "asd\nasd\nasd"
    assert fix_whitespace("{x} asd ") == "{x}asd"
    assert fix_whitespace("{x} asd {x} asd ") == "{x}asd {x} asd"
    assert fix_whitespace("{x} asd {x} \n {x}asd") == "{x}asd {x}\n{x}asd"


def test_fix_useless_ass_tags() -> None:
    assert fix_useless_ass_tags("{\\i0}asd") == "{\\i0}asd"
    assert fix_useless_ass_tags("{\\i1}asd") == "{\\i1}asd"
    assert fix_useless_ass_tags("asd{\\i1}asd{\\i1}asd") == "asd{\\i1}asdasd"
    assert fix_useless_ass_tags("{\\b0}asd") == "{\\b0}asd"
    assert fix_useless_ass_tags("{\\b1}asd") == "{\\b1}asd"
    assert fix_useless_ass_tags("asd{\\b1}asd{\\b1}asd") == "asd{\\b1}asdasd"
    assert (
        fix_useless_ass_tags("asd{\\b1}asd{\\b900}asd")
        == "asd{\\b1}asd{\\b900}asd"
    )
    assert (
        fix_useless_ass_tags("asd{\\b900}asd{\\b900}asd")
        == "asd{\\b900}asdasd"
    )
    assert fix_useless_ass_tags("asd{}asd") == "asdasd"


def test_fix_punctuation() -> None:
    assert fix_punctuation("asd...") == "asd\N{HORIZONTAL ELLIPSIS}"
    assert fix_punctuation("asd....") == "asd\N{HORIZONTAL ELLIPSIS}"
    assert (
        fix_punctuation("asd\N{HORIZONTAL ELLIPSIS}.")
        == "asd\N{HORIZONTAL ELLIPSIS}"
    )


def test_convert_to_smart_quotes() -> None:
    events = [
        AssEvent(text='"Infix". "Prefix…'),
        AssEvent(text="ignore"),
        AssEvent(text='…suffix"'),
    ]

    convert_to_smart_quotes(events, "„", "”")

    assert events[0].text == "„Infix”. „Prefix…"
    assert events[1].text == "ignore"
    assert events[2].text == "…suffix”"

    with pytest.raises(
        ProcessingError, match="uneven double quotation mark count"
    ):
        convert_to_smart_quotes(
            [AssEvent(text='"uneven quotation mark count')], "„", "”"
        )
