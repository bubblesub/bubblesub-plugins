import argparse
import asyncio
import concurrent.futures
import io
import time
import typing as T

from bubblesub.api import Api
from bubblesub.api.cmd import BaseCommand
from bubblesub.cfg.menu import MenuCommand, SubMenu
from bubblesub.cmd.common import SubtitlesSelection
from bubblesub.fmt.ass.event import AssEvent

try:
    import speech_recognition as sr
except ImportError as ex:
    raise CommandUnavailable(f"{ex.name} is not installed")

LEAD_IN = 100
LEAD_OUT = 100


def divide_into_groups(
    source: T.Sequence[T.Any], size: int
) -> T.Iterable[T.Sequence[T.Any]]:
    size = max(1, size)
    return (source[i : i + size] for i in range(0, len(source), size))


class SpeechRecognitionCommand(BaseCommand):
    names = ["sr", "google-speech-recognition"]
    help_text = (
        "Puts results of Google speech recognition "
        "for selected subtitles into their notes."
    )

    @property
    def is_enabled(self) -> bool:
        return (
            self.args.target.makes_sense
            and self.api.audio.current_stream
            and self.api.audio.current_stream.is_ready
        )

    async def run(self) -> None:
        await asyncio.get_event_loop().run_in_executor(
            None,
            self.run_in_background,
            await self.args.target.get_subtitles(),
        )

    def run_in_background(self, subtitles: T.List[AssEvent]) -> None:
        if self.args.audio:
            try:
                note = self.recognize_audio_selection()
            except sr.UnknownValueError:
                self.api.log.warn(f"not recognized")
            except sr.RequestError as ex:
                self.api.log.error(f"error ({ex})")
            else:
                self.api.log.info("OK")
                with self.api.undo.capture():
                    for subtitle in subtitles:
                        if subtitle.note:
                            subtitle.note += r"\N" + note
                        else:
                            subtitle.note = note
            return

        for i, subtitle_group in enumerate(
            divide_into_groups(subtitles, self.args.max_workers)
        ):
            if i:
                time.sleep(self.args.sleep_time)

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.args.max_workers
            ) as executor:
                future_to_sub = {
                    executor.submit(
                        self.recognize_subtitle, subtitle
                    ): subtitle
                    for subtitle in subtitle_group
                }

                completed, non_completed = concurrent.futures.wait(
                    future_to_sub, timeout=8
                )

                with self.api.undo.capture():
                    for future, subtitle in future_to_sub.items():
                        if future not in completed:
                            continue
                        try:
                            note = future.result()
                        except sr.UnknownValueError:
                            self.api.log.warn(
                                f"line #{subtitle.number}: not recognized"
                            )
                        except sr.RequestError as ex:
                            self.api.log.error(
                                f"line #{subtitle.number}: error ({ex})"
                            )
                        else:
                            self.api.log.info(f"line #{subtitle.number}: OK")
                            if subtitle.note:
                                subtitle.note += r"\N" + note
                            else:
                                subtitle.note = note

                for future, subtitle in future_to_sub.items():
                    if future in non_completed:
                        self.api.log.info(f"line #{subtitle.number}: timeout")

    def recognize_subtitle(self, subtitle: AssEvent) -> str:
        self.api.log.info(f"line #{subtitle.number} - analyzing")
        return self.recognize_audio(
            subtitle.start - LEAD_IN, subtitle.end + LEAD_OUT
        )

    def recognize_audio_selection(self) -> str:
        return self.recognize_audio(
            self.api.audio.view.selection_start - LEAD_IN,
            self.api.audio.view.selection_end + LEAD_OUT,
        )

    def recognize_audio(self, start: int, end: int) -> str:
        recognizer = sr.Recognizer()
        with io.BytesIO() as handle:
            self.api.audio.current_stream.save_wav(handle, start, end)
            handle.seek(0, io.SEEK_SET)
            with sr.AudioFile(handle) as source:
                audio = recognizer.record(source)
            return recognizer.recognize_google(audio, language=self.args.code)

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
            "-m",
            "--max-workers",
            help="number of parallel requests",
            type=int,
            default=5,
        )
        parser.add_argument(
            "-s",
            "--sleep-time",
            help="time to sleep after each chunk",
            type=int,
            default=0,
        )
        parser.add_argument(
            "-a",
            "--audio",
            help="process only audio selection",
            action="store_true",
        )
        parser.add_argument("code", help="language code")


COMMANDS = [SpeechRecognitionCommand]
MENU = [
    SubMenu(
        "&Speech recognition",
        [
            MenuCommand("&Japanese", "sr ja"),
            MenuCommand("&German", "sr de"),
            MenuCommand("&French", "sr fr"),
            MenuCommand("&Italian", "sr it"),
            MenuCommand("&Auto", "sr auto"),
        ],
    )
]
