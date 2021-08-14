from unittest.mock import Mock

import pytest
from ass_parser import AssEvent

from quality_check.check.durations import CheckDurations


@pytest.fixture
def check_durations(api: Mock) -> CheckDurations:
    return CheckDurations(api=api, renderer=Mock())


@pytest.mark.asyncio
async def test_check_durations_empty_text(
    check_durations: CheckDurations,
) -> None:
    event = AssEvent(start=0, end=100)
    check_durations.api.subs.events.append(event)
    check_durations.construct_event_map()
    results = [result async for result in check_durations.run_for_event(event)]
    assert len(results) == 0


@pytest.mark.asyncio
async def test_check_durations_comment(
    check_durations: CheckDurations,
) -> None:
    event = AssEvent(start=0, end=100, text="test", is_comment=True)
    check_durations.api.subs.events.append(event)
    check_durations.construct_event_map()
    results = [result async for result in check_durations.run_for_event(event)]
    assert len(results) == 0


@pytest.mark.asyncio
async def test_check_durations_too_short(
    check_durations: CheckDurations,
) -> None:
    event = AssEvent(start=0, end=100, text="test")
    check_durations.api.subs.events.append(event)
    check_durations.construct_event_map()
    results = [result async for result in check_durations.run_for_event(event)]
    assert len(results) == 1
    assert results[0].text == "duration shorter than 250 ms"


@pytest.mark.asyncio
async def test_check_durations_too_short_long_text(
    check_durations: CheckDurations,
) -> None:
    event = AssEvent(start=0, end=100, text="test test test test test")
    check_durations.api.subs.events.append(event)
    check_durations.construct_event_map()
    results = [result async for result in check_durations.run_for_event(event)]
    assert len(results) == 1
    assert results[0].text == "duration shorter than 500 ms"


@pytest.mark.asyncio
async def test_check_durations_good_duration(
    check_durations: CheckDurations,
) -> None:
    event = AssEvent(start=0, end=501, text="test test test test test")
    check_durations.api.subs.events.append(event)
    check_durations.construct_event_map()
    results = [result async for result in check_durations.run_for_event(event)]
    assert len(results) == 0


@pytest.mark.asyncio
async def test_check_durations_too_short_gap(
    check_durations: CheckDurations,
) -> None:
    event1 = AssEvent(start=0, end=500, text="test")
    event2 = AssEvent(start=600, end=900, text="test")
    check_durations.api.subs.events.append(event1)
    check_durations.api.subs.events.append(event2)
    check_durations.construct_event_map()
    results = [
        result async for result in check_durations.run_for_event(event1)
    ]
    assert len(results) == 1
    assert results[0].text == "gap shorter than 250 ms (100 ms)"


@pytest.mark.asyncio
async def test_check_durations_too_short_gap_empty_lines(
    check_durations: CheckDurations,
) -> None:
    event1 = AssEvent(start=0, end=500, text="test")
    event2 = AssEvent(start=550, end=550)
    event3 = AssEvent(start=600, end=900, text="test")
    check_durations.api.subs.events.append(event1)
    check_durations.api.subs.events.append(event2)
    check_durations.api.subs.events.append(event3)
    check_durations.construct_event_map()
    results = [
        result async for result in check_durations.run_for_event(event1)
    ]
    assert len(results) == 1
    assert results[0].text == "gap shorter than 250 ms (100 ms)"


@pytest.mark.asyncio
async def test_check_durations_too_short_gap_comments(
    check_durations: CheckDurations,
) -> None:
    event1 = AssEvent(start=0, end=500, text="test")
    event2 = AssEvent(start=550, end=550, text="test", is_comment=True)
    event3 = AssEvent(start=600, end=900, text="test")
    check_durations.api.subs.events.append(event1)
    check_durations.api.subs.events.append(event2)
    check_durations.api.subs.events.append(event3)
    check_durations.construct_event_map()
    results = [
        result async for result in check_durations.run_for_event(event1)
    ]
    assert len(results) == 1
    assert results[0].text == "gap shorter than 250 ms (100 ms)"


@pytest.mark.asyncio
async def test_check_durations_good_gap(
    check_durations: CheckDurations,
) -> None:
    event1 = AssEvent(start=0, end=500, text="test")
    event2 = AssEvent(start=750, end=900, text="test")
    check_durations.api.subs.events.append(event1)
    check_durations.api.subs.events.append(event2)
    check_durations.construct_event_map()
    results = [
        result async for result in check_durations.run_for_event(event1)
    ]
    assert len(results) == 0
