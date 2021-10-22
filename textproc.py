

import difflib


def strip_endline(s):
    return s if s[-1] != '\n' else s[:-1]


def character_distance(a: str, b: str) -> int:
    """
    Returns the number of changes that must be made to convert
    string a to string b.
    """
    count = 0
    for x in difflib.Differ().compare(f"{a}\n", f"{b}\n"):
        if x[0] == ' ':
            continue
        count += 1
    return count
