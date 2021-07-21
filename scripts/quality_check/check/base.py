import typing as T

from bubblesub.api import Api
from bubblesub.api.log import LogLevel
from bubblesub.ass_renderer import AssRenderer
from bubblesub.fmt.ass.event import AssEvent, AssEventList
from bubblesub.fmt.ass.meta import AssMeta
from bubblesub.fmt.ass.util import ass_to_plaintext


class BaseCheck:
    def __init__(self, api: Api) -> None:
        self.api = api

    def run(self) -> None:
        raise NotImplementedError("not implemented")

    @property
    def spell_check_lang(self) -> str:
        return self.api.subs.language or self.api.cfg.opt["gui"]["spell_check"]


class BaseResult:
    def __init__(
        self, event: T.Union[AssEvent, T.List[AssEvent]], text: str
    ) -> None:
        if isinstance(event, list):
            self.event = event[0]
            self.additional_events = event[1:]
        else:
            self.event = event
            self.additional_events = []
        self.text = text

    @property
    def events(self) -> T.Iterable[AssEvent]:
        yield self.event
        yield from self.additional_events

    def __repr__(self) -> str:
        ids = "+".join([f'#{event.number or "?"}' for event in self.events])
        return f"{ids}: {self.text}"


class DebugInformation(BaseResult):
    log_level = LogLevel.DEBUG


class Information(BaseResult):
    log_level = LogLevel.INFO


class Violation(BaseResult):
    log_level = LogLevel.WARNING


class BaseEventCheck(BaseCheck):
    def __init__(self, api: Api, renderer: AssRenderer) -> None:
        super().__init__(api)
        self.renderer = renderer

    def run(self) -> None:
        for result in self.get_violations():
            self.api.log.log(result.log_level, repr(result))

    def get_violations(self) -> None:
        for event in self.api.subs.events:
            yield from self.run_for_event(event)
