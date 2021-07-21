import typing as T

import numpy as np

from bubblesub.fmt.ass.event import AssEvent

from ..common import is_event_karaoke
from .base import BaseEventCheck, BaseResult, Violation


class CheckTimes(BaseEventCheck):
    WIDTH = 64
    HEIGHT = 48
    MAX_DISTANCE = 2
    MIN_RGB_DELTA = 3
    FRAME_CACHE: T.Dict[T.Tuple[str, int], np.float] = {}
    SNAP_CACHE: T.Dict[T.Tuple[str, int], bool] = {}

    async def run_for_event(self, event: AssEvent) -> T.Iterable[BaseResult]:
        if event.is_comment or is_event_karaoke(event):
            return

        if not await self.video_frame_snaps(event.start):
            yield Violation(event, "start does not snap to scene boundary")
        if not await self.video_frame_snaps(event.end):
            yield Violation(event, "end does not snap to scene boundary")

    async def get_video_frame_avg(self, frame_idx: int) -> np.float:
        cache_key = (self.api.video.current_stream.path, frame_idx)
        if cache_key not in self.FRAME_CACHE:
            self.FRAME_CACHE[cache_key] = np.mean(
                await self.api.video.current_stream.async_get_frame(
                    frame_idx, self.WIDTH, self.HEIGHT
                )
            )
        return self.FRAME_CACHE[cache_key]

    async def video_frame_snaps(self, pts: int) -> bool:
        cache_key = (self.api.video.current_stream.path, pts)
        if cache_key not in self.SNAP_CACHE:
            frame_idx = self.api.video.current_stream.frame_idx_from_pts(pts)

            frame_data = {}
            for delta in range(-self.MAX_DISTANCE, self.MAX_DISTANCE + 1):
                frame_data[delta] = await self.get_video_frame_avg(
                    frame_idx + delta
                )

            prev = frame_data[-self.MAX_DISTANCE]
            pivot = None
            for delta in range(-self.MAX_DISTANCE + 1, self.MAX_DISTANCE + 1):
                current = frame_data[delta]
                if abs(current - prev) > self.MIN_RGB_DELTA:
                    pivot = delta
                prev = current

            self.SNAP_CACHE[cache_key] = pivot is None or pivot == 0
        return self.SNAP_CACHE[cache_key]
