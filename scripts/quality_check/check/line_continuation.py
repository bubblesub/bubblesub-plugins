import typing as T

import regex

from bubblesub.api import Api
from bubblesub.ass_renderer import AssRenderer
from bubblesub.fmt.ass.event import AssEvent
from bubblesub.fmt.ass.util import ass_to_plaintext

from ..common import (
    WORDS_WITH_PERIOD,
    get_next_non_empty_event,
    get_prev_non_empty_event,
    is_event_dialog,
)
from .base import BaseEventCheck, BaseResult, Violation


class CheckLineContinuation(BaseEventCheck):
    def __init__(self, api: Api, renderer: AssRenderer) -> None:
        super().__init__(api, renderer)
        self.construct_event_map()

    def construct_event_map(self) -> None:
        non_empty_events = [
            event
            for event in self.api.subs.events
            if ass_to_plaintext(event.text) and not event.is_comment
        ]

        self.forwards_map = {}
        self.backwards_map = {}
        last: T.Optional[AssEvent] = None
        for event in non_empty_events:
            if last:
                self.forwards_map[last.index] = event
                self.backwards_map[event.index] = last
            last = event

    async def run_for_event(self, event: AssEvent) -> T.Iterable[BaseResult]:
        text = ass_to_plaintext(event.text)

        prev_event = self.backwards_map.get(event.index)
        next_event = self.forwards_map.get(event.index)
        next_text = ass_to_plaintext(next_event.text) if next_event else ""
        prev_text = ass_to_plaintext(prev_event.text) if prev_event else ""

        if text.endswith("…") and next_text.startswith("…"):
            yield Violation([event, next_event], "old-style line continuation")

        if (
            is_event_dialog(event)
            and not any(prev_text.endswith(word) for word in WORDS_WITH_PERIOD)
            and regex.search(r"\A\p{Ll}", text, flags=regex.M)
            and not regex.search(r"[,:\p{Ll}]\Z", prev_text, flags=regex.M)
        ):
            yield Violation(event, "sentence begins with a lowercase letter")

        if not event.is_comment and is_event_dialog(event):
            if regex.search(
                r"[,:\p{Ll}]\Z", text, flags=regex.M
            ) and not regex.search(
                r'\A(I\s|I\'(m|d|ll|ve)|\p{Ll}|[„”“"]\p{Lu})',
                next_text,
                flags=regex.M,
            ):
                yield Violation(event, "possibly unended sentence")
