import argparse
import asyncio
import subprocess
import tempfile
from pathlib import Path

from ass_parser import write_ass

from bubblesub.api import Api
from bubblesub.api.cmd import BaseCommand, CommandUnavailable
from bubblesub.cfg.menu import MenuCommand
from bubblesub.cmd.common import FancyPath, Pts
from bubblesub.util import ms_to_str


class SaveVideoSampleCommand(BaseCommand):
    names = ["save-video-sample"]
    help_text = "Saves given subtitles to a WEBM file."
    help_text_extra = (
        "Prompts user to choose where to save the file to if the path wasn't "
        "specified in the command arguments."
    )

    @property
    def is_enabled(self) -> bool:
        return (
            self.api.video.has_current_stream
            and self.api.video.current_stream.is_ready
        )

    async def run(self) -> None:
        start = await self.args.start.get()
        end = await self.args.end.get()
        if end < start:
            end, start = start, end
        if start == end:
            raise CommandUnavailable("nothing to sample")

        assert self.api.video.current_stream.path
        path = await self.args.path.get_save_path(
            file_filter="Webm Video File (*.webm)",
            default_file_name="video-{}-{}..{}.webm".format(
                self.api.video.current_stream.path.name,
                ms_to_str(start),
                ms_to_str(end),
            ),
        )

        def create_sample() -> None:
            with tempfile.TemporaryDirectory() as dir_name:
                subs_path = Path(dir_name) / "tmp.ass"
                with subs_path.open("w", encoding="utf-8") as handle:
                    write_ass(self.api.subs.ass_file, handle)

                command = [
                    "ffmpeg",
                    "-i",
                    str(self.api.video.current_stream.path),
                    "-y",
                    "-crf",
                    str(self.args.crf),
                    "-b:v",
                    "0",
                    "-ss",
                    ms_to_str(start),
                    "-to",
                    ms_to_str(end),
                ]

                if self.args.include_subs:
                    command += ["-vf", "ass=" + str(subs_path)]

                command += [str(path)]

                subprocess.run(command, check=False)

        # don't clog the UI thread
        self.api.log.info(f"saving video sample to {path}...")
        await asyncio.get_event_loop().run_in_executor(None, create_sample)
        self.api.log.info(f"saved video sample to {path}")

    @staticmethod
    def decorate_parser(api: Api, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--start",
            help="where the sample should start",
            type=lambda value: Pts(api, value),
            default="a.s",
        )
        parser.add_argument(
            "--end",
            help="where the sample should end",
            type=lambda value: Pts(api, value),
            default="a.e",
        )
        parser.add_argument(
            "-p",
            "--path",
            help="path to save the sample to",
            type=lambda value: FancyPath(api, value),
            default="",
        )
        parser.add_argument(
            "-i",
            "--include-subs",
            help='whether to "burn" subtitles into the video stream',
            action="store_true",
        )
        parser.add_argument(
            "--crf",
            help="constant rate factor parameter for ffmpeg (default: 20)",
            type=int,
            default=20,
        )


COMMANDS = [SaveVideoSampleCommand]
MENU = [MenuCommand("&Create video sample", "save-video-sample")]
