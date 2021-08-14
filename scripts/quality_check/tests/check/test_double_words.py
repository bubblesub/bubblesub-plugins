import typing as T
from unittest.mock import Mock

import pytest
from ass_parser import AssEvent

from quality_check.check.double_words import CheckDoubleWords


@pytest.fixture
def check_double_words(api: Mock) -> CheckDoubleWords:
    return CheckDoubleWords(api=api, renderer=Mock())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text, violation_text",
    [
        ("text", None),
        ("text text", "double word (text)"),
        ("text{} text", "double word (text)"),
        ("text{}\\Ntext", "double word (text)"),
        ("text{}text", None),
    ],
)
async def test_check_double_words(
    text: str,
    violation_text: T.Optional[str],
    check_double_words: CheckDoubleWords,
):
    event = AssEvent(text=text)
    check_double_words.api.subs.events.append(event)
    check_double_words.construct_event_map()
    results = [
        result async for result in check_double_words.run_for_event(event)
    ]
    if violation_text is None:
        assert len(results) == 0
    else:
        assert len(results) == 1
        assert results[0].text == violation_text
