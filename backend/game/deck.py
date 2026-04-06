import random

from game.constants import RANKS
from game.models import Card, SpecialType, Suit


NORMAL_SUITS = [Suit.JADE, Suit.SWORD, Suit.PAGODA, Suit.STAR]


def create_deck() -> list[Card]:
    cards: list[Card] = []
    for suit in NORMAL_SUITS:
        for rank in RANKS:
            cards.append(Card(suit=suit, rank=rank))
    for special in SpecialType:
        cards.append(Card(suit=Suit.SPECIAL, special=special))
    return cards


def shuffle_deck(deck: list[Card], rng: random.Random | None = None) -> list[Card]:
    shuffled = list(deck)
    if rng is None:
        random.shuffle(shuffled)
    else:
        rng.shuffle(shuffled)
    return shuffled


def deal(deck: list[Card], num_players: int = 4) -> list[list[Card]]:
    hands: list[list[Card]] = [[] for _ in range(num_players)]
    for i, card in enumerate(deck):
        hands[i % num_players].append(card)
    return hands
