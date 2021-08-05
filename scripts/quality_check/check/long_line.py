import typing as T

from bubblesub.api import Api
from bubblesub.ass_renderer import AssRenderer
from bubblesub.fmt.ass.event import AssEvent

from ..common import (
    WIDTH_MULTIPLIERS,
    get_optimal_line_heights,
    get_video_width,
    is_event_karaoke,
    measure_frame_size,
)
from .base import BaseEventCheck, BaseResult, Violation


class CheckLongLines(BaseEventCheck):
    def __init__(self, api: Api, renderer: AssRenderer) -> None:
        super().__init__(api, renderer)
        self.optimal_line_heights = get_optimal_line_heights(api)

    async def run_for_event(self, event: AssEvent) -> T.Iterable[BaseResult]:
        if is_event_karaoke(event):
            return

        width, height = measure_frame_size(self.api, self.renderer, event)
        average_height = self.optimal_line_heights.get(event.style, 0)
        line_count = round(height / average_height) if average_height else 0
        if not line_count:
            return

        try:
            width_multiplier = WIDTH_MULTIPLIERS[line_count]
        except LookupError:
            yield Violation(
                event,
                f"too many lines ({height}/{average_height} = {line_count})",
            )
        else:
            optimal_width = get_video_width(self.api) * width_multiplier
            if width > optimal_width:
                yield Violation(
                    event,
                    f"too long line "
                    f"({width - optimal_width:.02f} beyond {optimal_width:.02f})",
                )
