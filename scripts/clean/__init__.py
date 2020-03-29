import argparse

from bubblesub.api import Api
from bubblesub.api.cmd import BaseCommand
from bubblesub.cfg.menu import MenuCommand
from bubblesub.cmd.common import SubtitlesSelection

from .process import ProcessingError, convert_to_smart_quotes, fix_text


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

        parser.add_argument(
            "--smart-quotes",
            help="replace plain quotation marks with smart ones",
            action="store_true",
        )

        parser.add_argument(
            "--opening-quotation-mark",
            default="\N{LEFT DOUBLE QUOTATION MARK}",
        )
        parser.add_argument(
            "--closing-quotation-mark",
            default="\N{RIGHT DOUBLE QUOTATION MARK}",
        )

    async def run(self):
        changed = 0

        with self.api.undo.capture():
            subtitles = await self.args.target.get_subtitles()

            for sub in subtitles:
                style = self.api.subs.styles.get_by_name(sub.style)
                text = fix_text(sub.text, style)
                if text != sub.text:
                    sub.text = text
                    changed += 1

            self.api.log.info(f"fixed {changed} lines text")

            if self.args.smart_quotes:
                try:
                    changed = convert_to_smart_quotes(
                        subtitles,
                        self.args.opening_quotation_mark,
                        self.args.closing_quotation_mark,
                    )
                    self.api.log.info(f"fixed {changed} lines quotes")
                except ProcessingError as ex:
                    self.api.log.error(str(ex))


COMMANDS = [CleanCommand]
MENU = [MenuCommand("&Clean", "clean")]
