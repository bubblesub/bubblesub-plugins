from ..common import get_video_aspect_ratio, get_video_height, get_video_width
from .base import BaseCheck


class CheckVideoResolution(BaseCheck):
    async def run(self) -> None:
        width = get_video_width(self.api)
        height = get_video_height(self.api)
        aspect_ratio = get_video_aspect_ratio(self.api)
        if not width:
            self.api.log.error("Unknown video width.")
        if not height:
            self.api.log.error("Unknown video height.")
        if not aspect_ratio:
            self.api.log.error("Unknown aspect ratio.")
