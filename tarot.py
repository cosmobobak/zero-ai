from dataclasss import dataclass

@dataclass
class Card:
    name: str
    description: str

CARDS: "list[Card]" = [
    Card()
]