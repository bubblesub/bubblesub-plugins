import re
import typing as T

import ass_tag_parser
from ass_parser import AssEvent, AssStyle


class ProcessingError(Exception):
    pass


def fix_disjoint_ass_tags(text: str) -> str:
    return text.replace("}{", "")


def fix_dangling_ass_tags(text: str) -> str:
    return re.sub(r"{\\[bius][01]?}$", "", text)


def fix_bad_dialogue_dashes(text: str) -> str:
    try:
        ass_line = ass_tag_parser.parse_ass(text)
    except ass_tag_parser.ParseError:
        # dumb replace
        return re.sub("^- ", "\N{EN DASH} ", text, flags=re.M)
    else:
        plain_text_so_far = ""
        ret = ""
        for item in ass_line:
            chunk = item.meta.text
            if isinstance(item, ass_tag_parser.AssText):
                if chunk.startswith("- ") and (
                    plain_text_so_far.endswith("\n") or not plain_text_so_far
                ):
                    chunk = re.sub("^- ", "\N{EN DASH} ", chunk, flags=re.M)
                plain_text_so_far += chunk
            ret += chunk
        return ret


def fix_useless_ass_tags(text: str, style: T.Optional[AssStyle] = None) -> str:
    try:
        ass_line = ass_tag_parser.parse_ass(text)
    except ass_tag_parser.ParseError:
        return text

    def remove_useless_italics(
        ass_line: T.Iterable[ass_tag_parser.AssItem],
    ) -> T.Iterable[ass_tag_parser.AssItem]:
        last_state = style.italic if style else None
        for item in ass_line:
            if isinstance(item, ass_tag_parser.AssTagItalic):
                if last_state == item.enabled:
                    continue
                last_state = item.enabled
            yield item

    def remove_useless_bold(
        ass_line: T.Iterable[ass_tag_parser.AssItem],
    ) -> T.Iterable[ass_tag_parser.AssItem]:
        last_state = (style.bold if style else None), None
        for item in ass_line:
            if isinstance(item, ass_tag_parser.AssTagBold):
                if last_state == (item.enabled, item.weight):
                    continue
                last_state = item.enabled, item.weight
            yield item

    def remove_useless_alignment(
        ass_line: T.Iterable[ass_tag_parser.AssItem],
    ) -> T.Iterable[ass_tag_parser.AssItem]:
        last_state = style.alignment if style else None
        for item in ass_line:
            if isinstance(item, ass_tag_parser.AssTagAlignment):
                if last_state == item.alignment:
                    continue
                last_state = item.alignment
            yield item

    def remove_useless_karaoke(
        ass_line: T.Iterable[ass_tag_parser.AssItem],
    ) -> T.Iterable[ass_tag_parser.AssItem]:
        for item in ass_line:
            if (
                isinstance(item, ass_tag_parser.AssTagKaraoke)
                and item.duration == 0
            ):
                continue
            yield item

    ass_line = remove_useless_italics(ass_line)
    ass_line = remove_useless_bold(ass_line)
    ass_line = remove_useless_alignment(ass_line)
    ass_line = remove_useless_karaoke(ass_line)

    return ass_tag_parser.compose_ass(ass_line)


def fix_whitespace(text: str) -> str:
    try:
        ass_line = ass_tag_parser.parse_ass(text)
    except ass_tag_parser.ParseError:
        # dumb replace
        return re.sub(" *\n *", "\n", text.strip(), flags=re.M)

    for item in ass_line:
        if isinstance(item, ass_tag_parser.AssText):
            item.text = item.text.lstrip()
            break
    for item in reversed(ass_line):
        if isinstance(item, ass_tag_parser.AssText):
            item.text = item.text.rstrip()
            break
    for item in ass_line:
        if isinstance(item, ass_tag_parser.AssText):
            item.text = re.sub(" *\n *", "\n", item.text, flags=re.M)
    return ass_tag_parser.compose_ass(ass_line)


def fix_punctuation(text: str) -> str:
    text = text.replace("...", "\N{HORIZONTAL ELLIPSIS}")
    text = re.sub(
        "\N{HORIZONTAL ELLIPSIS}\\.+", "\N{HORIZONTAL ELLIPSIS}", text
    )
    return text


def fix_text(text: str, style: T.Optional[AssStyle] = None) -> str:
    text = text.replace("\\N", "\n")
    text = text.replace("\\n", "\n")

    text = fix_disjoint_ass_tags(text)
    text = fix_dangling_ass_tags(text)
    text = fix_useless_ass_tags(text, style)
    text = fix_bad_dialogue_dashes(text)
    text = fix_whitespace(text)
    text = fix_punctuation(text)

    text = text.replace("\n", "\\N")
    return text


def convert_to_smart_quotes(
    events: T.List[AssEvent], opening_mark: str, closing_mark: str
) -> int:
    count = 0
    for event in events:
        count += len(re.findall('["„“”]', event.text))
    if count % 2 != 0:
        raise ProcessingError("uneven double quotation mark count")

    count = 0
    opening = False
    for event in events:
        text = event.text
        matches = re.finditer('[„”“"]', text)
        for match in matches:
            new_quote = opening_mark if opening == 0 else closing_mark
            opening = not opening
            text = text[: match.start()] + new_quote + text[match.end() :]
        if event.text != text:
            event.text = text
            count += 1
    return count
