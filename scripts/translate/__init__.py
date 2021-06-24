import argparse
import asyncio
import time
import typing as T
from subprocess import PIPE, run

import ass_tag_parser
import requests

from bubblesub.api import Api
from bubblesub.api.cmd import BaseCommand
from bubblesub.cfg.menu import MenuCommand, SubMenu
from bubblesub.cmd.common import SubtitlesSelection
from bubblesub.fmt.ass.event import AssEvent

MAX_CHUNKS = 50


def divide_into_groups(
    source: T.Sequence[T.Any], size: int
) -> T.Iterable[T.Sequence[T.Any]]:
    size = max(1, size)
    return (source[i : i + size] for i in range(0, len(source), size))


def translate(
    api: Api,
    lines: T.List[str],
    engine: str,
    source_code: str,
    target_code: str,
) -> str:
    if not lines:
        return []

    if engine == "deepl":
        api_key = api.cfg.opt.get("plugins", {}).get("deepl_api_key")
        if not api_key:
            raise ValueError("missing plugins.deepl_api_key option.")
        response = requests.get(
            "https://api-free.deepl.com/v2/translate",
            data={
                "auth_key": api_key,
                "text": lines,
                "source_lang": source_code.upper(),
                "target_lang": target_code.upper(),
            },
        )
        response.raise_for_status()
        return [
            translation["text"]
            for translation in response.json()["translations"]
        ]
    else:
        args = ["trans", "-b"]
        args += ["-e", engine]
        args += ["-s", source_code]
        args += ["-t", target_code]
        args += ["\n".join(lines)]
        result = run(args, check=True, stdout=PIPE, stderr=PIPE)
        response = result.stdout.decode().strip()
        response = response.replace("u200b", "")
        if not response:
            raise ValueError("error")
        return response.split("\n")


def preprocess(chunk: str) -> str:
    return chunk.replace("\n", " ").replace("\\N", " ")


def postprocess(chunk: str) -> str:
    return (
        chunk.replace("...", "…")
        .replace(" !", "!")
        .replace(" ?", "?")
        .replace(" …", "…")
    )


def collect_text_chunks(events: T.List[AssEvent]) -> T.Iterable[str]:
    for event in events:
        text = event.note
        try:
            ass_line = ass_tag_parser.parse_ass(text)
        except ass_tag_parser.ParseError:
            if text:
                yield text
        else:
            for item in ass_line:
                if isinstance(item, ass_tag_parser.AssText) and item.text:
                    yield item.text


def put_text_chunks(events: T.List[AssEvent], chunks: T.List[str]) -> None:
    for event in events:
        text = event.note
        try:
            ass_line = ass_tag_parser.parse_ass(text)
        except ass_tag_parser.ParseError:
            text = chunks.pop(0)
        else:
            text = ""
            for item in ass_line:
                if isinstance(item, ass_tag_parser.AssText) and item.text:
                    text += chunks.pop(0)
                else:
                    text += item.meta.text
        if not text:
            continue
        if event.text:
            event.text += "\\N" + text
        else:
            event.text = text


class GoogleTranslateCommand(BaseCommand):
    names = ["tl", "google-translate"]
    help_text = "Puts results of Google translation into selected subtitles."

    @property
    def is_enabled(self) -> bool:
        return self.args.target.makes_sense

    async def run(self) -> None:
        await asyncio.get_event_loop().run_in_executor(
            None,
            self.run_in_background,
            await self.args.target.get_subtitles(),
        )

    def run_in_background(self, subs: T.List[AssEvent]) -> None:
        chunks = list(map(preprocess, collect_text_chunks(subs)))

        if not chunks:
            self.api.log.info("Nothing to translate")
            return

        i = 0
        translated_chunks: T.List[str] = []
        chunks_groups = list(divide_into_groups(chunks, MAX_CHUNKS))
        while chunks_groups:
            chunks_group = chunks_groups.pop(0)
            self.api.log.info(
                "translating chunks "
                f"{i+1}..{i+len(chunks_group)}/{len(chunks)}..."
            )
            i += len(chunks_group)

            try:
                translated_lines = translate(
                    self.api,
                    chunks_group,
                    self.args.engine,
                    self.args.source_code,
                    self.args.target_code,
                )
            except ValueError as ex:
                self.api.log.error(f"error ({ex})")
                return
            translated_chunks.extend(map(postprocess, translated_lines))

            if chunks_groups:
                time.sleep(self.args.sleep_time)

        if len(translated_chunks) != len(chunks):
            self.api.log.error("mismatching number of chunks")
            return

        self.api.log.info("OK")

        with self.api.undo.capture():
            put_text_chunks(subs, translated_chunks)

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
            "-e",
            "--engine",
            help="engine to use",
            choices=["bing", "deepl", "google", "yandex"],
            default="google",
        )
        parser.add_argument(
            "-s",
            "--sleep-time",
            help="time to sleep after each chunk",
            type=int,
            default=3,
        )
        parser.add_argument(
            metavar="from", dest="source_code", help="source language code"
        )
        parser.add_argument(
            metavar="to",
            dest="target_code",
            help="target language code",
            nargs="?",
            default="en",
        )


COMMANDS = [GoogleTranslateCommand]
MENU = [
    SubMenu(
        "&Translate",
        [
            MenuCommand("&Japanese", "tl ja"),
            MenuCommand("&German", "tl de"),
            MenuCommand("&French", "tl fr"),
            MenuCommand("&Italian", "tl it"),
            MenuCommand("&Polish", "tl pl"),
            MenuCommand("&Spanish", "tl es"),
            MenuCommand("&Auto", "tl auto"),
        ],
    )
]
