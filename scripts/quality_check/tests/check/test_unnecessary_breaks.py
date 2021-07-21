import typing as T
from unittest.mock import Mock, patch

import pytest

from bubblesub.fmt.ass.event import AssEvent

from quality_check.check.unnecessary_breaks import CheckUnnecessaryBreaks


@pytest.fixture
def check_unnecessary_breaks(api: Mock) -> CheckUnnecessaryBreaks:
    return CheckUnnecessaryBreaks(api=api, renderer=Mock())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text, violation_text",
    [
        ("text", None),
        ("text\\Ntext", "possibly unnecessary break (796.00 until 896.00)"),
        ("text.\\Ntext", None),
    ],
)
async def test_check_unnecessary_breaks(
    text: str,
    violation_text: T.Optional[str],
    check_unnecessary_breaks: CheckUnnecessaryBreaks,
):
    event = AssEvent(text=text)
    check_unnecessary_breaks.api.subs.events.append(event)
    check_unnecessary_breaks.construct_event_map()

    with patch(
        "quality_check.check.unnecessary_breaks.measure_frame_size",
        return_value=(100, 0),
    ):
        results = [
            result
            async for result in check_unnecessary_breaks.run_for_event(event)
        ]

    if violation_text is None:
        assert len(results) == 0
    else:
        assert len(results) == 1
        assert results[0].text == violation_text
