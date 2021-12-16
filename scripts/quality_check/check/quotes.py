import re
import typing as T

from ass_parser import AssEvent
from ass_tag_parser import ass_to_plaintext

from .base import (
    BaseEventCheck,
    BaseResult,
    DebugInformation,
    Information,
    Violation,
)


class CheckQuotes(BaseEventCheck):
    async def run_for_event(self, event: AssEvent) -> T.Iterable[BaseResult]:
        text = ass_to_plaintext(event.text)

        if text.count('"'):
            yield Information(event, "plain quotation mark")

        if (
            (text.count("„") + text.count("“")) != text.count("”")
        ) or text.count('"') % 2 == 1:
            yield Information(event, "partial quote")
            return

        if re.search(r'[:,]["”]', text):
            yield Violation(event, "punctuation inside quotation marks")

        if re.search(r'["”][\.,…?!]', text, flags=re.M):
            yield DebugInformation(
                event, "punctuation outside quotation marks"
            )

        if re.search(r'[a-z]\s[„“"].+[\.…?!]["”]', text, flags=re.M):
            yield Violation(event, "punctuation inside quotation marks")
        elif re.search(r'[„“"].+[\.…?!]["”]', text, flags=re.M):
            yield DebugInformation(event, "punctuation inside quotation marks")
