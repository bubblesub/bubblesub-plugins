import functools
import re

import ass_tag_parser
from ass_tag_parser import ass_to_plaintext

from bubblesub.api.cmd import BaseCommand
from bubblesub.cfg.menu import MenuCommand

STRIP = list("…–—♪") + ["\\N"]


def ms_to_str(ms: int) -> str:
    return str(ms // 1000)


def extract_text(text: str) -> str:
    ret = ass_to_plaintext(text)
    return functools.reduce(
        lambda ret, word: ret.replace(word, ""), STRIP, ret
    ).strip()


class ProgressCommand(BaseCommand):
    names = ["progress"]
    help_text = "Shows basic statistics about subtitles translation progress."
    help_text_extra = (
        "Expects that the subtitles are already timed "
        "and untranslated lines are empty."
    )

    async def run(self):
        empty_count = 0
        empty_duration = 0
        total_count = 0
        total_duration = 0
        words = []
        for event in self.api.subs.events:
            if event.is_comment:
                continue
            total_duration += event.duration
            total_count += 1
            text = extract_text(event.text)
            if not text:
                empty_duration += event.duration
                empty_count += 1
            else:
                words += list(re.findall("[a-zA-Z]+", text))

        self.api.log.info(
            f"{empty_count} lines left ("
            f"{total_count - empty_count}/{max(1, total_count)}, "
            f"{(total_count - empty_count) / max(1, total_count):.01%})"
        )
        self.api.log.info(
            f"{ms_to_str(empty_duration)} seconds left ("
            f"{ms_to_str(total_duration - empty_duration)}/"
            f"{ms_to_str(total_duration)}, "
            f"{(total_duration - empty_duration) / max(1, total_duration):.01%})"
        )
        self.api.log.info(f"{len(words)} words translated")
        self.api.log.info(f"{sum(map(len, words))} characters translated")


COMMANDS = [ProgressCommand]
MENU = [MenuCommand("Show translation &progress", "progress")]
