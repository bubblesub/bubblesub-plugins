import enum
import typing as T
from contextlib import contextmanager
from copy import copy
from datetime import datetime

from bubblesub.api import Api
from bubblesub.ass_renderer import AssRenderer
from bubblesub.fmt.ass.event import AssEvent, AssEventList
from bubblesub.fmt.ass.meta import AssMeta


class AspectRatio(enum.Enum):
    AR_4_3 = enum.auto()
    AR_16_9 = enum.auto()


WIDTH_MULTIPLIERS = {1: 0.7, 2: 0.9}

NON_STUTTER_PREFIXES = {"half", "well"}
NON_STUTTER_SUFFIXES = {"kun", "san", "chan", "smaa", "senpai", "sensei"}
NON_STUTTER_WORDS = {
    "bye-bye",
    "easy-peasy",
    "heh-heh",
    "one-two",
    "part-time",
    "peek-a-boo",
    "ta-da",
    "ta-dah",
    "uh-huh",
    "uh-oh",
}
WORDS_WITH_PERIOD = {"vs.", "Mrs.", "Mr.", "Jr.", "U.F.O.", "a.k.a."}


def measure_frame_size(
    api: Api, renderer: AssRenderer, event: AssEvent
) -> T.Tuple[int, int]:
    if not any(style.name == event.style for style in renderer.style_list):
        return (0, 0)

    fake_event_list = AssEventList()
    fake_event_list.append(copy(event))

    renderer.set_source(
        style_list=renderer.style_list,
        event_list=fake_event_list,
        meta=renderer.meta,
        video_resolution=renderer.video_resolution,
    )

    layers = [
        layer
        for layer in renderer.render_raw(time=event.start)
        if layer.type == 0
    ]
    if not layers:
        return (0, 0)
    min_x = min(layer.dst_x for layer in layers)
    min_y = min(layer.dst_y for layer in layers)
    max_x = max(layer.dst_x + layer.w for layer in layers)
    max_y = max(layer.dst_y + layer.h for layer in layers)
    aspect_ratio = (
        api.video.current_stream.aspect_ratio
        if api.video.current_stream
        else 1
    )
    return (int((max_x - min_x) * aspect_ratio), max_y - min_y)


def get_optimal_line_heights(api: Api) -> T.Dict[str, float]:
    TEST_LINE_COUNT = 20
    VIDEO_RES_X = 100
    VIDEO_RES_Y = TEST_LINE_COUNT * 300

    fake_meta = AssMeta()
    fake_meta.set("WrapStyle", 2)
    renderer = AssRenderer()
    renderer.set_source(
        style_list=api.subs.styles,
        event_list=api.subs.events,
        meta=fake_meta,
        video_resolution=(VIDEO_RES_X, VIDEO_RES_Y),
    )

    ret = {}
    for style in api.subs.styles:
        event = AssEvent(
            start=0,
            end=1000,
            text="\\N".join(["gjMW"] * TEST_LINE_COUNT),
            style=style.name,
        )

        _frame_width, frame_height = measure_frame_size(api, renderer, event)
        line_height = frame_height / TEST_LINE_COUNT
        ret[event.style] = line_height
        api.log.debug(f"average height for {event.style}: {line_height}")
    return ret


def get_video_height(api: Api) -> int:
    return int(api.subs.meta.get("PlayResY", "0"))


def get_video_width(api: Api) -> int:
    return int(api.subs.meta.get("PlayResX", "0"))


def strip_brackets(text: str) -> str:
    return text.lstrip("[(").rstrip(")]")


def is_event_sign(event: AssEvent) -> bool:
    return strip_brackets(event.actor) in {
        "sign",
        "episode title",
        "series title",
    }


def is_event_title(event: AssEvent) -> bool:
    return strip_brackets(event.actor) == "title"


def is_event_karaoke(event: AssEvent) -> bool:
    return strip_brackets(event.actor) == "karaoke"


def is_event_credits(event: AssEvent) -> bool:
    return strip_brackets(event.actor) == "credits"


def is_event_dialog(event: AssEvent) -> bool:
    return not (
        is_event_sign(event)
        or is_event_title(event)
        or is_event_karaoke(event)
        or is_event_credits(event)
    )


def get_video_aspect_ratio(api: Api) -> T.Optional[AspectRatio]:
    width = get_video_width(api)
    height = get_video_height(api)
    if not width or not height:
        return None

    epsilon = 0.03
    mapping = {
        4 / 3: AspectRatio.AR_4_3,
        16 / 9: AspectRatio.AR_16_9,
    }
    for value, enum_value in mapping.items():
        if abs(width / height - value) < epsilon:
            return enum_value
    return None


@contextmanager
def benchmark(api: Api, message: str) -> None:
    start = datetime.now()
    yield
    end = datetime.now()
    duration = end - start
    api.log.debug(f"{message}: {duration}")
