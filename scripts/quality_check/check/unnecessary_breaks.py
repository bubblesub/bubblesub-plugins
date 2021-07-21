import re
import typing as T
from copy import copy

from bubblesub.fmt.ass.event import AssEvent

from ..common import (
    WIDTH_MULTIPLIERS,
    get_width,
    is_event_karaoke,
    is_event_title,
    measure_frame_size,
)
from .base import BaseEventCheck, BaseResult, Information


class CheckUnnecessaryBreaks(BaseEventCheck):
    async def run_for_event(self, event: AssEvent) -> T.Iterable[BaseResult]:
        if r"\N" not in event.text:
            return

        event_copy = copy(event)
        event_copy.text = event.text.replace(r"\N", " ")
        width, _height = measure_frame_size(
            self.api, self.renderer, event_copy
        )
        optimal_width = get_width(self.api) * WIDTH_MULTIPLIERS[1]

        many_sentences = (
            len(re.split(r"[\.!?…—] ", event_copy.text)) > 1
            or event_copy.text.count("–") >= 2
        )
        if (
            width < optimal_width
            and not many_sentences
            and not is_event_title(event)
            and not is_event_karaoke(event)
        ):
            yield Information(
                event,
                f"possibly unnecessary break "
                f"({optimal_width - width:.02f} until {optimal_width:.02f})",
            )
