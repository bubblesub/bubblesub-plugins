from bubblesub.fmt.ass.event import AssEvent, AssEventList

from quality_check.check import Violation


def test_violation_single_event() -> None:
    event_list = AssEventList()
    event_list.append(AssEvent(start=0, end=0))
    violation = Violation(event_list[0], "test")
    assert repr(violation) == "#1: test"


def test_violation_multiple_events() -> None:
    event_list = AssEventList()
    event_list.append(AssEvent(start=0, end=0))
    event_list.append(AssEvent(start=0, end=0))
    violation = Violation([event_list[0], event_list[1]], "test")
    assert repr(violation) == "#1+#2: test"
