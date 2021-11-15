from dataclasses import dataclass

@dataclass
class Card:
    name: str
    meaning: str
    meaning_reversed: str
    answer: str
    long_form_meaning: str


