import re
import typing as T

from bubblesub.fmt.ass.event import AssEvent
from bubblesub.fmt.ass.util import ass_to_plaintext

from .base import BaseEventCheck, BaseResult, Violation


class CheckDoubleWords(BaseEventCheck):
    async def run_for_event(self, event: AssEvent) -> T.Iterable[BaseResult]:
        text = ass_to_plaintext(event.text)

        for pair in re.finditer(r"(?<!\w)(\w+)\s+\1(?!\w)", text):
            word = pair.group(1)
            yield Violation(event, f"double word ({word})")
