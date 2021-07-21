import typing as T
from unittest.mock import Mock

import pytest

from bubblesub.fmt.ass.event import AssEvent

from quality_check.check.punctuation import CheckPunctuation


@pytest.fixture
def check_punctuation() -> CheckPunctuation:
    return CheckPunctuation(api=Mock(), renderer=Mock())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text, violation_text",
    [
        ("Text\\N", "extra line break"),
        ("\\NText", "extra line break"),
        ("Text\\NText\\NText", "three or more lines"),
        ("Text\\N Text", "whitespace around line break"),
        ("Text \\NText", "whitespace around line break"),
        ("Text ", "extra whitespace"),
        (" Text", "extra whitespace"),
        ("Text  text", "double space"),
        ("...", "bad ellipsis (expected …)"),
        ("What youve done", "missing apostrophe"),
        ("- What?\\N- No!", "bad dash (expected \N{EN DASH})"),
        (
            "\N{EM DASH}What?\\N\N{EM DASH}No!",
            "bad dash (expected \N{EN DASH})",
        ),
        ("\N{EM DASH}What?", "bad dash (expected \N{EN DASH})"),
        ("\N{EN DASH} Title \N{EN DASH}", "bad dash (expected \N{EM DASH})"),
        ("\N{EM DASH}Title\N{EM DASH}", None),
        ("\N{EM DASH}Whatever\N{EM DASH}…", "bad dash (expected \N{EN DASH})"),
        ("- What?", "bad dash (expected \N{EN DASH})"),
        ("\N{EN DASH} What!", "dialog with just one person"),
        ("blabla \N{EM DASH}", "whitespace around \N{EM DASH}"),
        ("blabla \N{EM DASH}blabla", "whitespace around \N{EM DASH}"),
        ("blabla\N{EM DASH} blabla", "whitespace around \N{EM DASH}"),
        ("blabla\N{EM DASH} Blabla", None),
        ("\N{EN DASH} What! \N{EN DASH} Nothing\\Nat all.", None),
        ("\N{EN DASH} What. \N{EN DASH} Nothing\\Nat all.", None),
        ("\N{EN DASH} What? \N{EN DASH} Nothing\\Nat all.", None),
        ("\N{EN DASH} What… \N{EN DASH} Nothing\\Nat all.", None),
        (
            "\N{EN DASH} What \N{EN DASH} Nothing\\Nat all.",
            "dialog with just one person",
        ),
        (
            "\N{EN DASH} What.\N{EN DASH} Nothing\\Nat all.",
            "dialog with just one person",
        ),
        (
            "\N{EN DASH} What: \N{EN DASH} Nothing\\Nat all.",
            "dialog with just one person",
        ),
        ("\N{EN DASH} What!\\N\N{EN DASH} Nothing.", None),
        ("What--", "bad dash (expected \N{EM DASH})"),
        ("What\N{EN DASH}", "bad dash (expected \N{EM DASH})"),
        ("W-what?", "possibly wrong stutter capitalization"),
        ("Ta-da!", None),
        ("Peek-a-boo!", None),
        ("Ayuhara-san", None),
        ("What! what…", "lowercase letter after sentence end"),
        ("What. what…", "lowercase letter after sentence end"),
        ("Japan vs. the world", None),
        ("Japan vss. the world", "lowercase letter after sentence end"),
        ("What? what…", "lowercase letter after sentence end"),
        ("What , no.", "whitespace before punctuation"),
        ("What …", "whitespace before punctuation"),
        ("What !", "whitespace before punctuation"),
        ("What .", "whitespace before punctuation"),
        ("What ?", "whitespace before punctuation"),
        ("What :", "whitespace before punctuation"),
        ("What ;", "whitespace before punctuation"),
        ("What\\N, no.", "line break before punctuation"),
        ("What\\N…no.", "line break before punctuation"),
        ("What\\N!", "line break before punctuation"),
        ("What\\N.", "line break before punctuation"),
        ("What\\N?", "line break before punctuation"),
        ("What\\N:", "line break before punctuation"),
        ("What\\N;", "line break before punctuation"),
        ("What?No!", "missing whitespace after punctuation mark"),
        ("What!No!", "missing whitespace after punctuation mark"),
        ("What.No!", "missing whitespace after punctuation mark"),
        ("What,no!", "missing whitespace after punctuation mark"),
        ("What:no!", "missing whitespace after punctuation mark"),
        ("What;no!", "missing whitespace after punctuation mark"),
        ("What…no!", "missing whitespace after punctuation mark"),
        ("What? No!", None),
        ("What! No!", None),
        ("What. No!", None),
        ("What, no!", None),
        ("What: no!", None),
        ("What; no!", None),
        ("What… no!", None),
        ("What?\\NNo!", None),
        ("What!\\NNo!", None),
        ("What.\\NNo!", None),
        ("What,\\Nno!", None),
        ("What:\\Nno!", None),
        ("What;\\Nno!", None),
        ("What…\\Nno!", None),
        ("test\ttest", "unrecognized whitespace"),
        ("test\N{ZERO WIDTH SPACE}test", "unrecognized whitespace"),
        ("….", "extra comma or dot"),
        (",.", "extra comma or dot"),
        ("?.", "extra comma or dot"),
        ("!.", "extra comma or dot"),
        (":.", "extra comma or dot"),
        (";.", "extra comma or dot"),
        ("…,", "extra comma or dot"),
        (",,", "extra comma or dot"),
        ("?,", "extra comma or dot"),
        ("!,", "extra comma or dot"),
        (":,", "extra comma or dot"),
        (";,", "extra comma or dot"),
    ],
)
async def test_check_punctuation(
    text: str,
    violation_text: T.Optional[str],
    check_punctuation: CheckPunctuation,
) -> None:
    event = AssEvent(text=text)
    results = [
        result async for result in check_punctuation.run_for_event(event)
    ]
    if violation_text is None:
        assert len(results) == 0
    else:
        assert len(results) == 1
        assert results[0].text == violation_text
