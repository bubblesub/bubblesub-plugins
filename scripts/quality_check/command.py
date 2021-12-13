import argparse
import bisect
from collections.abc import Iterable

from bubblesub.api import Api
from bubblesub.api.cmd import BaseCommand
from bubblesub.api.log import LogLevel
from bubblesub.ass_renderer import AssRenderer

from .check import (
    BaseCheck,
    BaseResult,
    CheckActorStats,
    CheckAssTags,
    CheckDoubleWords,
    CheckDurations,
    CheckFonts,
    CheckGrammar,
    CheckLineContinuation,
    CheckLongLines,
    CheckPunctuation,
    CheckPunctuationStats,
    CheckQuotes,
    CheckSpelling,
    CheckStyleStats,
    CheckStyleValidity,
    CheckTimes,
    CheckUnnecessaryBreaks,
    CheckVideoResolution,
)
from .check.fonts import get_fonts
from .common import benchmark, get_video_height, get_video_width


def get_event_checks(full: bool) -> Iterable[BaseCheck]:
    if full:
        yield CheckGrammar

    yield CheckStyleValidity
    yield CheckAssTags
    yield CheckDurations
    yield CheckPunctuation
    yield CheckQuotes
    yield CheckLineContinuation
    yield CheckDoubleWords
    yield CheckUnnecessaryBreaks
    yield CheckLongLines

    if full:
        yield CheckTimes


def get_global_checks(full: bool) -> Iterable[BaseCheck]:
    yield CheckVideoResolution
    yield CheckSpelling
    yield CheckActorStats
    yield CheckStyleStats
    yield CheckFonts
    yield CheckPunctuationStats


async def list_violations(
    api: Api, checks: Iterable[BaseCheck]
) -> Iterable[BaseResult]:
    renderer = AssRenderer()
    renderer.set_source(
        ass_file=api.subs.ass_file,
        video_resolution=(get_video_width(api), get_video_height(api)),
    )

    for check_cls in checks:
        with benchmark(api, f"{check_cls}"):
            check = check_cls(api, renderer)
            async for violation in check.get_violations():
                yield violation


class QualityCheckCommand(BaseCommand):
    names = ["qc", "quality-check"]
    help_text = "Tries to pinpoint common issues with the subtitles."

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

        event_checks = get_event_checks(full=self.args.full)
        global_checks = get_global_checks(full=self.args.full)

        if self.args.focus_prev or self.args.focus_next:
            violations = [
                result
                async for result in list_violations(self.api, event_checks)
                if result.log_level in {LogLevel.WARNING, LogLevel.ERROR}
            ]
            if not violations:
                return
            violated_indexes = sorted(
                violation.event.index for violation in violations
            )

            if self.args.focus_prev:
                selected_index = self.api.subs.selected_indexes[0]
                next_index = violated_indexes[
                    bisect.bisect_left(violated_indexes, selected_index) - 1
                ]

            elif self.args.focus_next:
                selected_index = self.api.subs.selected_indexes[-1]
                next_index = violated_indexes[
                    bisect.bisect_right(violated_indexes, selected_index)
                    % len(violated_indexes)
                ]

            else:
                raise AssertionError

            self.api.subs.selected_indexes = [next_index]
            for result in violations:
                if result.event.index == next_index:
                    self.api.log.log(result.log_level, repr(result))
            return

        async for result in list_violations(self.api, event_checks):
            self.api.log.log(result.log_level, repr(result))

        for check_cls in global_checks:
            with benchmark(self.api, f"{check_cls}"):
                check = check_cls(self.api)
                await check.run()
