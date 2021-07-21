import typing as T
from unittest.mock import Mock

import pytest

from bubblesub.fmt.ass.event import AssEvent, AssEventList
from quality_check.check.double_words import CheckDoubleWords


@pytest.fixture
def check_double_words() -> CheckDoubleWords:
    return CheckDoubleWords(api=Mock(), renderer=Mock())


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
    event_list = AssEventList()
    event_list.append(AssEvent(text=text))
    results = [
        result
        async for result in check_double_words.run_for_event(event_list[0])
    ]
    if violation_text is None:
        assert len(results) == 0
    else:
        assert len(results) == 1
        assert results[0].text == violation_text
