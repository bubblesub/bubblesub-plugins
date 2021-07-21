from unittest.mock import Mock

import pytest

from bubblesub.fmt.ass.event import AssEvent, AssEventList
from quality_check.check.durations import CheckDurations


@pytest.fixture
def check_durations() -> CheckDurations:
    return CheckDurations(api=Mock(), renderer=Mock())


def test_check_durations_empty_text(check_durations: CheckDurations) -> None:
    event = AssEvent(start=0, end=100)
    assert len(list(check_durations.run_for_event(event))) == 0


def test_check_durations_comment(check_durations: CheckDurations) -> None:
    event = AssEvent(start=0, end=100, text="test", is_comment=True)
    assert len(list(check_durations.run_for_event(event))) == 0


def test_check_durations_too_short(check_durations: CheckDurations) -> None:
    event = AssEvent(start=0, end=100, text="test")
    results = list(check_durations.run_for_event(event))
    assert len(results) == 1
    assert results[0].text == "duration shorter than 250 ms"


def test_check_durations_too_short_long_text(
    check_durations: CheckDurations,
) -> None:
    event = AssEvent(start=0, end=100, text="test test test test test")
    results = list(check_durations.run_for_event(event))
    assert len(results) == 1
    assert results[0].text == "duration shorter than 500 ms"


def test_check_durations_good_duration(
    check_durations: CheckDurations,
) -> None:
    event = AssEvent(start=0, end=501, text="test test test test test")
    assert len(list(check_durations.run_for_event(event))) == 0


def test_check_durations_too_short_gap(
    check_durations: CheckDurations,
) -> None:
    event_list = AssEventList()
    event_list.append(AssEvent(start=0, end=500, text="test"))
    event_list.append(AssEvent(start=600, end=900, text="test"))
    results = list(check_durations.run_for_event(event_list[0]))
    assert len(results) == 1
    assert results[0].text == "gap shorter than 250 ms (100 ms)"


def test_check_durations_too_short_gap_empty_lines(
    check_durations: CheckDurations,
) -> None:
    event_list = AssEventList()
    event_list.append(AssEvent(start=0, end=500, text="test"))
    event_list.append(AssEvent(start=550, end=550))
    event_list.append(AssEvent(start=600, end=900, text="test"))
    results = list(check_durations.run_for_event(event_list[0]))
    assert len(results) == 1
    assert results[0].text == "gap shorter than 250 ms (100 ms)"


def test_check_durations_too_short_gap_comments(
    check_durations: CheckDurations,
) -> None:
    event_list = AssEventList()
    event_list.append(AssEvent(start=0, end=500, text="test"))
    event_list.append(
        AssEvent(start=550, end=550, text="test", is_comment=True)
    )
    event_list.append(AssEvent(start=600, end=900, text="test"))
    results = list(check_durations.run_for_event(event_list[0]))
    assert len(results) == 1
    assert results[0].text == "gap shorter than 250 ms (100 ms)"


def test_check_durations_good_gap(check_durations: CheckDurations) -> None:
    event_list = AssEventList()
    event_list.append(AssEvent(start=0, end=500, text="test"))
    event_list.append(AssEvent(start=750, end=900, text="test"))
    assert len(list(check_durations.run_for_event(event_list[0]))) == 0
