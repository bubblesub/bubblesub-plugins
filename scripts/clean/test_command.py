import re
import typing as T

import pytest

from .process import (
    fix_bad_dialogue_dashes,
    fix_dangling_ass_tags,
    fix_disjoint_ass_tags,
    fix_punctuation,
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


def test_punctuation() -> None:
    assert fix_punctuation("asd...") == "asd\N{HORIZONTAL ELLIPSIS}"
