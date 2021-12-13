import asyncio
import typing as T
from unittest.mock import Mock, patch

import pytest
from ass_parser import AssEvent

from quality_check.check.times import CheckTimes


@pytest.fixture(name="check_times")
def fixture_check_times(api: Mock) -> CheckTimes:
    return CheckTimes(api=api, renderer=Mock())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "frame_brightness_values, expected_violation",
    [
        pytest.param((100, 100, 100, 100, 100), False, id="flat neighborhood"),
        pytest.param((0, 100, 100, 100, 100), True, id="1 frame early"),
        pytest.param((0, 0, 100, 100, 100), False, id="ideal fit"),
        pytest.param((0, 0, 0, 100, 100), True, id="1 frame late"),
        pytest.param((0, 0, 0, 0, 100), True, id="2 frames late"),
        pytest.param((0, 0, 0, 0, 0), False, id="flat neighborhood"),
        pytest.param((0, 1, 100, 100, 100), False, id="ignore small changes"),
        pytest.param(
            (0, 5, 100, 93, 94), False, id="biggest change on scene boundary"
        ),
        pytest.param(
            (0, 25, 26, 27, 26), True, id="biggest change 1 frame early"
        ),
    ],
)
async def test_check_times(
    frame_brightness_values: T.Tuple[int],
    expected_violation: bool,
    check_times: CheckTimes,
) -> None:
    event = AssEvent(start=2, end=2)
    check_times.api.video.current_stream.frame_idx_from_pts = lambda pts: pts

    class MockGetVideoFrameAvg:
        def __call__(self, frame_idx):
            future = asyncio.get_event_loop().create_future()
            future.set_result(frame_brightness_values[frame_idx])
            return future

    check_times.api.subs.events.append(event)
    check_times.construct_event_map()

    with patch(
        "quality_check.check.times.CheckTimes.get_video_frame_avg",
        new_callable=MockGetVideoFrameAvg,
    ):
        results = [result async for result in check_times.run_for_event(event)]

    if expected_violation:
        assert results
    else:
        assert not results
