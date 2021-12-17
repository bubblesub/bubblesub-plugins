import argparse
import bisect
from collections.abc import Iterable

from ass_lint.checks import get_checks
from ass_lint.checks.fonts import get_fonts
from ass_lint.common import BaseCheck, BaseResult, CheckContext
from ass_lint.common import LogLevel as AssLintLogLevel
from ass_lint.util import benchmark, get_video_height, get_video_width
from ass_lint.video import VideoError, VideoSource
from ass_renderer import AssRenderer

from bubblesub.api import Api
from bubblesub.api.cmd import BaseCommand
from bubblesub.api.log import LogLevel
from bubblesub.cfg.menu import MenuCommand


async def list_violations(
    api: Api, ctx: CheckContext, checks: Iterable[BaseCheck]
) -> Iterable[BaseResult]:
    for check_cls in checks:
        with benchmark(f"{check_cls}"):
            try:
                check = check_cls(ctx)
            except Exception as ex:
                api.log.warning(ex)
            else:
                async for result in check.run():
                    yield result


class QualityCheckCommand(BaseCommand):
    names = ["qc", "quality-check"]
    help_text = "Tries to pinpoint common issues with the subtitles."
    video_cache = {}
    renderer = AssRenderer()

    @staticmethod
    def decorate_parser(api: Api, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("-p", "--focus-prev", action="store_true")
        parser.add_argument("-n", "--focus-next", action="store_true")
        parser.add_argument(
            "-nc",
            action="store_true",
            dest="clear_cache",
            help="clear font cache",
        )
        parser.add_argument(
            "-f",
            "--full",
            action="store_true",
            help="run slower checks",
        )

    async def run(self):
        if self.args.clear_cache:
            get_fonts.cache_clear()

        ass_file = self.api.subs.ass_file
        video_resolution = (
            self.api.video.current_stream.width,
            self.api.video.current_stream.height,
        )

        self.renderer.set_source(
            ass_file=ass_file, video_resolution=video_resolution
        )

        video = None
        if video_path := self.api.video.current_stream.path:
            if not (video := self.video_cache.get(video_path)):
                try:
                    video = VideoSource(video_path)
                except VideoError as ex:
                    log.api.warning(ex)
                self.video_cache[video_path] = video

        context = CheckContext(
            subs_path=self.api.subs.path,
            ass_file=ass_file,
            video_resolution=video_resolution,
            renderer=self.renderer,
            video=video,
        )
        checks = list(get_checks(full=self.args.full))

        if self.args.focus_prev or self.args.focus_next:
            violations = [
                result
                async for result in list_violations(self.api, context, checks)
                if result.log_level in [AssLintLogLevel.warning]
            ]
            if not violations:
                return
            violated_indexes = sorted(
                violation.events[0].index
                for violation in violations
                if violation.events
            )

            if self.args.focus_prev:
                selected_index = (
                    self.api.subs.selected_indexes[0]
                    if self.api.subs.selected_indexes
                    else -1
                )
                new_index = violated_indexes[
                    bisect.bisect_left(violated_indexes, selected_index) - 1
                ]

            elif self.args.focus_next:
                selected_index = (
                    self.api.subs.selected_indexes[-1]
                    if self.api.subs.selected_indexes
                    else -1
                )
                new_index = violated_indexes[
                    bisect.bisect_right(violated_indexes, selected_index)
                    % len(violated_indexes)
                ]

            else:
                raise AssertionError

            self.api.subs.selected_indexes = [new_index]
            for result in violations:
                if result.events and result.events[0].index == new_index:
                    self.log_result(result)
            return

        async for result in list_violations(self.api, context, checks):
            self.log_result(result)

    def log_result(self, result: BaseResult) -> None:
        log_level = {
            AssLintLogLevel.warning: LogLevel.WARNING,
            AssLintLogLevel.debug: LogLevel.DEBUG,
            AssLintLogLevel.info: LogLevel.INFO,
        }[result.log_level]
        self.api.log.log(log_level, repr(result))


COMMANDS = [QualityCheckCommand]
MENU = [MenuCommand("&Quality check", "qc")]
