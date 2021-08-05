import re
import typing as T
from copy import copy

from bubblesub.api import Api
from bubblesub.ass_renderer import AssRenderer
from bubblesub.fmt.ass.event import AssEvent

from ..common import (
    WIDTH_MULTIPLIERS,
    get_video_aspect_ratio,
    get_video_width,
    is_event_karaoke,
    is_event_title,
    measure_frame_size,
)
from .base import BaseEventCheck, BaseResult, Information


class CheckUnnecessaryBreaks(BaseEventCheck):
    def __init__(self, api: Api, renderer: AssRenderer) -> None:
        super().__init__(api, renderer)
        self.optimal_width: T.Optional[float] = None
        aspect_ratio = get_video_aspect_ratio(api)
        if aspect_ratio:
            self.optimal_width = (
                get_video_width(api) * WIDTH_MULTIPLIERS[aspect_ratio][1]
            )

    async def run_for_event(self, event: AssEvent) -> T.Iterable[BaseResult]:
        if self.optimal_width is None:
            # AR information unavailable, covered by a separate check
            return

        if r"\N" not in event.text:
            return

        event_copy = copy(event)
        event_copy.text = event.text.replace(r"\N", " ")
        width, _height = measure_frame_size(
            self.api, self.renderer, event_copy
        )

        many_sentences = (
            len(re.split(r"[\.!?…—] ", event_copy.text)) > 1
            or event_copy.text.count("–") >= 2
        )
        if (
            width < self.optimal_width
            and not many_sentences
            and not is_event_title(event)
            and not is_event_karaoke(event)
        ):
            yield Information(
                event,
                f"possibly unnecessary break "
                f"({self.optimal_width - width:.02f} until {self.optimal_width:.02f})",
            )
