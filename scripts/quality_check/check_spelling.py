import re
import typing as T
from collections import defaultdict

from bubblesub.api import Api
from bubblesub.fmt.ass.util import ass_to_plaintext, spell_check_ass_line
from bubblesub.spell_check import (
    BaseSpellChecker,
    SpellCheckerError,
    create_spell_checker,
)

from .common import is_event_karaoke


class WordList:
    def __init__(self) -> None:
        self.case_insensitive: T.List[str] = []
        self.case_sensitive: T.List[str] = []

    def add_word(self, word: str) -> None:
        if word.islower():
            self.case_insensitive.append(word.lower())
        else:
            self.case_sensitive.append(word)

    def __contains__(self, word: str) -> None:
        return (
            word in self.case_sensitive
            or word.lower() in self.case_insensitive
        )


class SpellCheckerProxy(BaseSpellChecker):
    def __init__(
        self, spell_checker: BaseSpellChecker, whitelist: WordList
    ) -> None:
        self.spell_checker = spell_checker
        self.whitelist = whitelist

    def check(self, word: str) -> bool:
        return self.spell_checker.check(word) or word in self.whitelist

    def add(self, word: str) -> None:
        raise NotImplementedError("not implemented")

    def add_to_session(self, word: str) -> None:
        raise NotImplementedError("not implemented")

    def suggest(self, word: str) -> T.Iterable[str]:
        raise NotImplementedError("not implemented")


def check_spelling(spell_check_lang: T.Optional[str], api: Api) -> None:
    if not api.subs.path:
        return

    if not spell_check_lang:
        api.log.warn("Spell check was disabled in config.")
        return

    whitelist = WordList()
    spell_check_lang_short = re.sub("[-_].*", "", spell_check_lang)

    dict_names = [
        f"dict-{spell_check_lang}.txt",
        f"dict-{spell_check_lang_short}.txt",
        f"{spell_check_lang}-dict.txt",
        f"{spell_check_lang_short}-dict.txt",
        "dict.txt",
    ]
    for dict_name in dict_names:
        dict_path = api.subs.path.with_name(dict_name)
        if dict_path.exists():
            for line in dict_path.read_text().splitlines():
                whitelist.add_word(line)
            break

    try:
        base_spell_checker = create_spell_checker(spell_check_lang)
        custom_spell_checker = SpellCheckerProxy(base_spell_checker, whitelist)
    except SpellCheckerError as ex:
        api.log.error(str(ex))
        return

    misspelling_map = defaultdict(set)
    for event in api.subs.events:
        if is_event_karaoke(event):
            continue
        text = ass_to_plaintext(event.text)
        for _start, _end, word in spell_check_ass_line(
            custom_spell_checker, text
        ):
            misspelling_map[word].add(event.number)

    if misspelling_map:
        api.log.info("Misspelled words:")
        for word, line_numbers in sorted(
            misspelling_map.items(),
            key=lambda item: len(item[1]),
            reverse=True,
        ):
            api.log.warn(
                f"- {word}: " + ", ".join(f"#{num}" for num in line_numbers)
            )
    else:
        api.log.info("No misspelled words")
