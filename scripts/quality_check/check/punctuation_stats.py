from collections import defaultdict

from bubblesub.fmt.ass.util import ass_to_plaintext

from ..common import is_event_karaoke, is_event_title
from .base import BaseCheck


class CheckPunctuationStats(BaseCheck):
    CHARS = "!…"

    async def run(self) -> None:
        stats = defaultdict(int)
        for event in self.api.subs.events:
            if is_event_title(event) or is_event_karaoke(event):
                continue
            for char in self.CHARS:
                stats[char] += ass_to_plaintext(event.text).count(char)

        self.api.log.info(
            "Punctuation stats: "
            + ", ".join(f"{char}: {count}" for char, count in stats.items())
        )
