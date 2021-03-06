import typing as T

import regex

from bubblesub.fmt.ass.event import AssEvent
from bubblesub.fmt.ass.util import ass_to_plaintext

from .common import (
    WORDS_WITH_PERIOD,
    BaseResult,
    Violation,
    get_next_non_empty_event,
    get_prev_non_empty_event,
    is_event_dialog,
)


def check_line_continuation(event: AssEvent) -> T.Iterable[BaseResult]:
    text = ass_to_plaintext(event.text)

    prev_event = get_prev_non_empty_event(event)
    next_event = get_next_non_empty_event(event)
    next_text = ass_to_plaintext(next_event.text) if next_event else ""
    prev_text = ass_to_plaintext(prev_event.text) if prev_event else ""

    if text.endswith("…") and next_text.startswith("…"):
        yield Violation([event, next_event], "old-style line continuation")

    if (
        regex.search(r"\A\p{Ll}", text, flags=regex.M)
        and is_event_dialog(event)
        and not regex.search(r"[,:\p{Ll}]\Z", prev_text, flags=regex.M)
        and not any(prev_text.endswith(word) for word in WORDS_WITH_PERIOD)
    ):
        yield Violation(event, "sentence begins with a lowercase letter")

    if not event.is_comment and is_event_dialog(event):
        if regex.search(
            r"[,:\p{Ll}]\Z", text, flags=regex.M
        ) and not regex.search(
            r'\A(I\s|I\'(m|d|ll)|\p{Ll}|[„”“"]\p{Lu})',
            next_text,
            flags=regex.M,
        ):
            yield Violation(event, "possibly unended sentence")
