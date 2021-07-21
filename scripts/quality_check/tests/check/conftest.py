from unittest.mock import Mock

import pytest

from bubblesub.fmt.ass.event import AssEventList


@pytest.fixture
def api() -> Mock:
    return Mock(
        subs=Mock(
            events=AssEventList(),
            meta={"PlayResX": 1280},
        ),
        video=Mock(
            current_stream=Mock(aspect_ratio=1),
        ),
    )
