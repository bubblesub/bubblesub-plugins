import re
import typing as T
from unittest.mock import Mock

import pytest

from bubblesub.api.log import LogLevel
from bubblesub.fmt.ass.event import AssEvent

from quality_check.check.quotes import CheckQuotes


@pytest.fixture
def check_quotes(api: Mock) -> CheckQuotes:
    return CheckQuotes(api=api, renderer=Mock())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text, expected_violations",
    [
        ("„What…", [("partial quote", LogLevel.INFO)]),
        ("…what.”", [("partial quote", LogLevel.INFO)]),
        ("„What.”", [(".*inside.*marks", LogLevel.DEBUG)]),
        ("„What”.", [(".*outside.*", LogLevel.DEBUG)]),
        ("„What”, he said.", [(".*outside.*", LogLevel.DEBUG)]),
        ("„What.” he said.", [(".*inside.*", LogLevel.DEBUG)]),
        ("„What!” he said.", [(".*inside.*", LogLevel.DEBUG)]),
        ("„What?” he said.", [(".*inside.*", LogLevel.DEBUG)]),
        ("„What…” he said.", [(".*inside.*", LogLevel.DEBUG)]),
        ("„What,” he said.", [(".*inside.*", LogLevel.WARNING)]),
        ("He said „what.”", [(".*inside.*", LogLevel.WARNING)]),
        ("He said „what!”", [(".*inside.*", LogLevel.WARNING)]),
        ("He said „what?”", [(".*inside.*", LogLevel.WARNING)]),
        ("He said „what…”", [(".*inside.*", LogLevel.WARNING)]),
        ('"What"', [("plain quotation mark", LogLevel.INFO)]),
        (
            '"What…',
            [
                ("plain quotation mark", LogLevel.INFO),
                ("partial quote", LogLevel.INFO),
            ],
        ),
        (
            '…what."',
            [
                ("plain quotation mark", LogLevel.INFO),
                ("partial quote", LogLevel.INFO),
            ],
        ),
        (
            '"What."',
            [
                ("plain quotation mark", LogLevel.INFO),
                (".*inside.*marks", LogLevel.DEBUG),
            ],
        ),
        (
            '"What".',
            [
                ("plain quotation mark", LogLevel.INFO),
                (".*outside.*", LogLevel.DEBUG),
            ],
        ),
        (
            '"What", he said.',
            [
                ("plain quotation mark", LogLevel.INFO),
                (".*outside.*", LogLevel.DEBUG),
            ],
        ),
        (
            '"What." he said.',
            [
                ("plain quotation mark", LogLevel.INFO),
                (".*inside.*", LogLevel.DEBUG),
            ],
        ),
        (
            '"What!" he said.',
            [
                ("plain quotation mark", LogLevel.INFO),
                (".*inside.*", LogLevel.DEBUG),
            ],
        ),
        (
            '"What?" he said.',
            [
                ("plain quotation mark", LogLevel.INFO),
                (".*inside.*", LogLevel.DEBUG),
            ],
        ),
        (
            '"What…" he said.',
            [
                ("plain quotation mark", LogLevel.INFO),
                (".*inside.*", LogLevel.DEBUG),
            ],
        ),
        (
            '"What," he said.',
            [
                ("plain quotation mark", LogLevel.INFO),
                (".*inside.*", LogLevel.WARNING),
            ],
        ),
        (
            'He said "what."',
            [
                ("plain quotation mark", LogLevel.INFO),
                (".*inside.*", LogLevel.WARNING),
            ],
        ),
        (
            'He said "what!"',
            [
                ("plain quotation mark", LogLevel.INFO),
                (".*inside.*", LogLevel.WARNING),
            ],
        ),
        (
            'He said "what?"',
            [
                ("plain quotation mark", LogLevel.INFO),
                (".*inside.*", LogLevel.WARNING),
            ],
        ),
        (
            'He said "what…"',
            [
                ("plain quotation mark", LogLevel.INFO),
                (".*inside.*", LogLevel.WARNING),
            ],
        ),
    ],
)
async def test_check_quotes(
    text: str,
    expected_violations: T.List[T.Tuple[str, LogLevel]],
    check_quotes: CheckQuotes,
) -> None:
    event = AssEvent(text=text)
    check_quotes.api.subs.events.append(event)
    check_quotes.construct_event_map()
    results = [result async for result in check_quotes.run_for_event(event)]
    assert len(results) == len(expected_violations)
    for expected_violation, result in zip(expected_violations, results):
        violation_text_re, log_level = expected_violation
        assert re.match(violation_text_re, result.text)
        assert result.log_level == log_level
