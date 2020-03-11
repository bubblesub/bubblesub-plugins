import re
import typing as T

import ass_tag_parser


def fix_disjoint_ass_tags(text: str) -> str:
    return text.replace("}{", "")


def fix_dangling_ass_tags(text: str) -> str:
    return re.sub(r"{\\[bius][01]?}$", "", text)


def fix_bad_dialogue_dashes(text: str) -> str:
    try:
        ass_line = ass_tag_parser.parse_ass(text)
    except ass_tag_parser.ParseError as ex:
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


def fix_useless_ass_tags(text: str) -> str:
    try:
        ass_line = ass_tag_parser.parse_ass(text)
    except ass_tag_parser.ParseError as ex:
        return text

    def remove_useless_italics(
        ass_line: T.Iterable[ass_tag_parser.AssItem],
    ) -> T.Iterable[ass_tag_parser.AssItem]:
        last_state = None
        for item in ass_line:
            if isinstance(item, ass_tag_parser.AssTagItalic):
                if last_state == item.enabled:
                    continue
                last_state = item.enabled
            yield item

    def remove_useless_bold(
        ass_line: T.Iterable[ass_tag_parser.AssItem],
    ) -> T.Iterable[ass_tag_parser.AssItem]:
        last_state = None, None
        for item in ass_line:
            if isinstance(item, ass_tag_parser.AssTagBold):
                if last_state == (item.enabled, item.weight):
                    continue
                last_state = item.enabled, item.weight
            yield item

    ass_line = remove_useless_italics(ass_line)
    ass_line = remove_useless_bold(ass_line)

    return ass_tag_parser.compose_ass(ass_line)


def fix_whitespace(text: str) -> str:
    try:
        ass_line = ass_tag_parser.parse_ass(text)
    except ass_tag_parser.ParseError as ex:
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
    return text.replace("...", "\N{HORIZONTAL ELLIPSIS}")


def fix_text(text: str) -> str:
    text = text.replace("\\N", "\n")
    text = text.replace("\\n", "\n")

    text = fix_disjoint_ass_tags(text)
    text = fix_dangling_ass_tags(text)
    text = fix_useless_ass_tags(text)
    text = fix_bad_dialogue_dashes(text)
    text = fix_whitespace(text)
    text = fix_punctuation(text)

    text = text.replace("\n", "\\N")
    return text
