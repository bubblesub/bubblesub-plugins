import typing as T

import numpy as np
from ass_parser import AssEvent

from ..common import is_event_karaoke
from .base import BaseEventCheck, BaseResult, Violation


def format_delta(delta: int) -> str:
    if delta >= 0:
        return f"+{delta}"
    return f"{delta}"


class CheckTimes(BaseEventCheck):
    """This check verifies if the subtitles snap to scene boundaries up to
    `MAX_DISTANCE` frames. A scene boundary is understood to be when the camera
    in the video changes from one scene to another.
    """

    WIDTH = 4
    HEIGHT = 3
    MAX_DISTANCE = 2
    MIN_RGB_DELTA = 25
    FRAME_CACHE: T.Dict[T.Tuple[str, int], float] = {}
    SNAP_CACHE: T.Dict[T.Tuple[str, int], bool] = {}

    async def run_for_event(self, event: AssEvent) -> T.Iterable[BaseResult]:
        if event.is_comment or is_event_karaoke(event):
            return

        delta = await self.get_best_pivot(event.start)
        if delta:
            yield Violation(
                event,
                f"start does not snap to scene boundary ({format_delta(delta)}f)",
            )
        delta = await self.get_best_pivot(event.end)
        if delta:
            yield Violation(
                event,
                f"end does not snap to scene boundary ({format_delta(delta)}f)",
            )

    async def get_video_frame_avg(self, frame_idx: int) -> T.Optional[float]:
        cache_key = (self.api.video.current_stream.path.absolute(), frame_idx)
        if cache_key not in self.FRAME_CACHE:
            ret = await self.api.video.current_stream.async_get_frame(
                frame_idx, self.WIDTH, self.HEIGHT
            )
            self.FRAME_CACHE[cache_key] = (
                ret.astype(np.int16) if ret is not None else None
            )
        return self.FRAME_CACHE[cache_key]

    async def get_best_pivot(self, pts: int) -> T.Optional[int]:
        cache_key = (self.api.video.current_stream.path, pts)
        if cache_key not in self.SNAP_CACHE:
            frame_idx = self.api.video.current_stream.frame_idx_from_pts(pts)

            frame_data = {}
            for delta in range(-self.MAX_DISTANCE, self.MAX_DISTANCE + 1):
                frame_data[delta] = await self.get_video_frame_avg(
                    frame_idx + delta
                )

            prev = frame_data[-self.MAX_DISTANCE]
            pivots: T.List[T.Tuple[int, float]] = []
            for delta in range(-self.MAX_DISTANCE + 1, self.MAX_DISTANCE + 1):
                current = frame_data[delta]
                if current is not None and prev is not None:
                    diff = np.mean(np.abs(current - prev))
                    if diff >= self.MIN_RGB_DELTA:
                        pivots.append((delta, diff))
                prev = current

            if pivots:
                best_pivot, best_diff = max(
                    sorted(pivots), key=lambda kv: kv[1]
                )
            else:
                best_pivot, best_diff = None, None

            self.SNAP_CACHE[cache_key] = best_pivot
        return self.SNAP_CACHE[cache_key]
