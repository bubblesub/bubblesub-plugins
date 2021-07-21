import typing as T
from unittest.mock import Mock, patch

import pytest

from bubblesub.fmt.ass.event import AssEvent, AssEventList
from quality_check.check.unnecessary_breaks import CheckUnnecessaryBreaks


@pytest.fixture
def check_unnecessary_breaks() -> CheckUnnecessaryBreaks:
    api = Mock()
    api.video.current_stream.aspect_ratio = 1
    api.subs.meta = {"PlayResX": 1280}
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
    with patch(
        "quality_check.check.unnecessary_breaks.measure_frame_size",
        return_value=(100, 0),
    ):
        event_list = AssEventList()
        event_list.append(AssEvent(text=text))
        results = [
            result
            async for result in check_unnecessary_breaks.run_for_event(
                event_list[0]
            )
        ]

    if violation_text is None:
        assert len(results) == 0
    else:
        assert len(results) == 1
        assert results[0].text == violation_text
