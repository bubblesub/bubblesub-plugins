import typing as T

from bubblesub.fmt.ass.event import AssEvent
from bubblesub.fmt.ass.style import AssStyleList

from .base import BaseEventCheck, BaseResult, Violation


class CheckStyleValidity(BaseEventCheck):
    async def run_for_event(self, event: AssEvent) -> T.Iterable[BaseResult]:
        if (
            event.style.startswith("[")
            and event.style.endswith("]")
            and event.is_comment
        ):
            return

        style = self.api.subs.styles.get_by_name(event.style)
        if style is None:
            yield Violation(event, "using non-existing style")
