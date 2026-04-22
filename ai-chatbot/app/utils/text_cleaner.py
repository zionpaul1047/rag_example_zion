import re


ALLOWED_SPECIALS_PATTERN = r"[^0-9A-Za-z가-힣\s\.\,\!\?\-\+\:\/\(\)\[\]#&~]"


def normalize_newlines(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text


def remove_control_characters(text: str) -> str:
    return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)


def clean_special_characters(text: str) -> str:
    """
    의미 없는 특수문자는 제거하되,
    문서 의미에 자주 쓰이는 기호는 일부 유지한다.
    유지 예:
    . , ! ? - + : / ( ) [ ] # &
    """
    return re.sub(ALLOWED_SPECIALS_PATTERN, " ", text)


def collapse_spaces(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def should_drop_line(line: str) -> bool:
    stripped = line.strip()

    if not stripped:
        return True

    # 단독 페이지 번호
    if re.fullmatch(r"\d{1,4}", stripped):
        return True

    # 점만 반복되거나 목차 연결선 같은 형태
    if re.fullmatch(r"[\.\-_·•●○]{2,}", stripped):
        return True

    # 너무 짧고 정보량이 거의 없는 줄
    if len(stripped) <= 1:
        return True

    return False


def clean_lines(text: str) -> str:
    lines = text.split("\n")
    cleaned = []

    for line in lines:
        line = line.strip()

        if should_drop_line(line):
            continue

        # 줄 내부 공백 정리
        line = re.sub(r"\s+", " ", line).strip()

        if line:
            cleaned.append(line)

    return "\n".join(cleaned)


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = normalize_newlines(text)
    text = remove_control_characters(text)
    text = clean_special_characters(text)
    text = clean_lines(text)
    text = collapse_spaces(text)

    return text