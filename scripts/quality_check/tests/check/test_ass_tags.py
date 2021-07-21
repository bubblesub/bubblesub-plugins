import re
import typing as T
from unittest.mock import Mock

import pytest

from bubblesub.fmt.ass.event import AssEvent, AssEventList
from quality_check.check.ass_tags import CheckAssTags


@pytest.fixture
def check_ass_tags() -> CheckAssTags:
    return CheckAssTags(api=Mock(), renderer=Mock())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text, violation_text_re",
    [
        ("text", None),
        ("{\\an8}", None),
        ("text{\\b1}text", None),
        ("{\\fsherp}", "invalid syntax (.*)"),
        ("{}", "pointless tag"),
        ("{\\\\comment}", "use notes to make comments"),
        ("{\\comment}", "invalid syntax (.*)"),
        ("{\\a5}", "using legacy alignment tag"),
        ("{\\an8comment}", "invalid syntax (.*)"),
        ("{comment\\an8}", "use notes to make comments"),
        ("{\\k20}{\\k20}", None),
        ("{\\an8}{\\fs5}", "disjointed tags"),
    ],
)
async def test_check_ass_tags(
    text: str, violation_text_re: T.Optional[str], check_ass_tags: CheckAssTags
):
    event_list = AssEventList()
    event_list.append(AssEvent(text=text))
    results = [
        result async for result in check_ass_tags.run_for_event(event_list[0])
    ]
    if violation_text_re is None:
        assert len(results) == 0
    else:
        assert len(results) == 1
        assert re.match(violation_text_re, results[0].text)
