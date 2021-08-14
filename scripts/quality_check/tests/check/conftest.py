from unittest.mock import Mock

import pytest
from ass_parser import AssEventList


@pytest.fixture
def api() -> Mock:
    return Mock(
        subs=Mock(
            events=AssEventList(),
            script_info={"PlayResX": 1280},
        ),
        video=Mock(
            current_stream=Mock(aspect_ratio=1),
        ),
    )
