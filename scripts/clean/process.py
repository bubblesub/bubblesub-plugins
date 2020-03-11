import re


def fix_disjoint_ass_tags(text: str) -> str:
    return text.replace("}{", "")


def fix_dangling_ass_tags(text: str) -> str:
    return re.sub(r"{\\[bius][01]?}$", "", text)


def fix_bad_dialogue_dashes(text: str) -> str:
    return re.sub("^- ", "\N{EN DASH} ", text, flags=re.M)


def fix_whitespace(text: str) -> str:
    text = text.strip()
    text = text.replace("\n ", "\n")
    text = text.replace(" \n", "\n")
    return text


def fix_punctuation(text: str) -> str:
    return text.replace("...", "\N{HORIZONTAL ELLIPSIS}")


def fix_text(text: str) -> str:
    text = text.replace("\\N", "\n")
    text = text.replace("\\n", "\n")

    text = fix_disjoint_ass_tags(text)
    text = fix_dangling_ass_tags(text)
    text = fix_bad_dialogue_dashes(text)
    text = fix_whitespace(text)
    text = fix_punctuation(text)

    text = text.replace("\n", "\\N")
    return text
