from game.models import Card, Suit, SpecialType


def make_card(rank: int, suit: str = "jade") -> Card:
    return Card(suit=Suit(suit), rank=rank)


def phoenix() -> Card:
    return Card(suit=Suit.SPECIAL, special=SpecialType.PHOENIX)


def dragon() -> Card:
    return Card(suit=Suit.SPECIAL, special=SpecialType.DRAGON)


def hound() -> Card:
    return Card(suit=Suit.SPECIAL, special=SpecialType.HOUND)


def mah_jong() -> Card:
    return Card(suit=Suit.SPECIAL, special=SpecialType.MAH_JONG)


def make_cards(*specs: tuple[int, str]) -> list[Card]:
    """Create multiple cards from (rank, suit) tuples."""
    return [make_card(rank, suit) for rank, suit in specs]
