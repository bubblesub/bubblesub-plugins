import argparse

from bubblesub.api import Api
from bubblesub.api.cmd import BaseCommand
from bubblesub.cfg.menu import MenuCommand
from bubblesub.cmd.common import SubtitlesSelection

from .process import fix_text


class CleanCommand(BaseCommand):
    names = ["clean"]
    help_text = "Cleans subtitles from random garbage."

    @property
    def is_enabled(self):
        return self.args.target.makes_sense

    @staticmethod
    def decorate_parser(api: Api, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "-t",
            "--target",
            help="subtitles to process",
            type=lambda value: SubtitlesSelection(api, value),
            default="selected",
        )

    async def run(self):
        changed = 0
        with self.api.undo.capture():
            for sub in await self.args.target.get_subtitles():
                text = fix_text(sub.text)
                if text != sub.text:
                    sub.text = text
                    changed += 1
        self.api.log.info(f"fixed {changed} lines")


COMMANDS = [CleanCommand]
MENU = [MenuCommand("&Clean", "clean")]
