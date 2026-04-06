from __future__ import annotations

from collections import Counter

from game.constants import MIN_PAIR_SEQUENCE_PAIRS, MIN_STRAIGHT_LENGTH
from game.models import Card, Combination, CombinationType, SpecialType


def detect_combination(cards: list[Card]) -> Combination | None:
    if not cards:
        return None

    n = len(cards)

    if n == 1:
        return _detect_single(cards[0])

    phoenix = None
    normal_cards: list[Card] = []
    has_dragon = False
    has_hound = False

    for card in cards:
        if card.special == SpecialType.PHOENIX:
            phoenix = card
        elif card.special == SpecialType.DRAGON:
            has_dragon = True
        elif card.special == SpecialType.HOUND:
            has_hound = True
        else:
            normal_cards.append(card)

    if has_dragon or has_hound:
        return None

    bomb = _detect_bomb(cards, normal_cards, phoenix)
    if bomb is not None:
        return bomb

    mah_jong_cards = [c for c in normal_cards if c.special == SpecialType.MAH_JONG]
    rankable_cards = [c for c in normal_cards if c.special != SpecialType.MAH_JONG]

    rank_counts: dict[int, list[Card]] = {}
    for card in rankable_cards:
        rank_counts.setdefault(card.rank, []).append(card)

    has_phoenix = phoenix is not None
    has_mah_jong = len(mah_jong_cards) > 0

    if n == 2:
        return _detect_pair(rank_counts, has_phoenix, has_mah_jong, cards)

    if n == 3:
        return _detect_triple(rank_counts, has_phoenix, has_mah_jong, cards)

    if n == 5:
        full_house = _detect_full_house(rank_counts, has_phoenix, has_mah_jong, cards)
        if full_house is not None:
            return full_house

    if n >= 4 and n % 2 == 0:
        pair_seq = _detect_pair_sequence(rank_counts, has_phoenix, has_mah_jong, cards)
        if pair_seq is not None:
            return pair_seq

    if n >= MIN_STRAIGHT_LENGTH:
        straight = _detect_straight(rank_counts, has_phoenix, has_mah_jong, cards)
        if straight is not None:
            return straight

    return None


def can_play_on(play: Combination, current_trick: Combination | None) -> bool:
    if current_trick is None:
        return True

    if play.type == CombinationType.HOUND_LEAD:
        return False

    is_phoenix_single = (
        play.type == CombinationType.SINGLE
        and len(play.cards) == 1
        and play.cards[0].special == SpecialType.PHOENIX
    )
    is_dragon_single = (
        current_trick.type == CombinationType.SINGLE
        and len(current_trick.cards) == 1
        and current_trick.cards[0].special == SpecialType.DRAGON
    )
    if is_phoenix_single and is_dragon_single:
        return False

    return play.beats(current_trick)


def _detect_single(card: Card) -> Combination:
    if card.special == SpecialType.HOUND:
        return Combination(
            type=CombinationType.HOUND_LEAD,
            cards=[card],
            rank=0,
            length=1,
        )
    if card.special == SpecialType.DRAGON:
        return Combination(
            type=CombinationType.SINGLE,
            cards=[card],
            rank=15.0,
            length=1,
        )
    if card.special == SpecialType.PHOENIX:
        return Combination(
            type=CombinationType.SINGLE,
            cards=[card],
            rank=14.5,
            length=1,
        )
    if card.special == SpecialType.MAH_JONG:
        return Combination(
            type=CombinationType.SINGLE,
            cards=[card],
            rank=1.0,
            length=1,
        )
    return Combination(
        type=CombinationType.SINGLE,
        cards=[card],
        rank=float(card.rank),
        length=1,
    )


def _detect_bomb(
    all_cards: list[Card],
    normal_cards: list[Card],
    phoenix: Card | None,
) -> Combination | None:
    if phoenix is not None:
        return None

    n = len(all_cards)
    non_special = [c for c in normal_cards if not c.is_special]

    if n == 4 and len(non_special) == 4:
        ranks = {c.rank for c in non_special}
        if len(ranks) == 1:
            return Combination(
                type=CombinationType.FOUR_BOMB,
                cards=all_cards,
                rank=float(non_special[0].rank),
                length=4,
                is_bomb=True,
            )

    if n >= MIN_STRAIGHT_LENGTH and len(non_special) == n:
        suits = {c.suit for c in non_special}
        if len(suits) == 1:
            sorted_ranks = sorted(c.rank for c in non_special)
            if _is_consecutive(sorted_ranks):
                return Combination(
                    type=CombinationType.STRAIGHT_BOMB,
                    cards=all_cards,
                    rank=float(sorted_ranks[-1]),
                    length=n,
                    is_bomb=True,
                )

    return None


def _detect_pair(
    rank_counts: dict[int, list[Card]],
    has_phoenix: bool,
    has_mah_jong: bool,
    cards: list[Card],
) -> Combination | None:
    if has_mah_jong:
        return None

    if has_phoenix:
        if len(rank_counts) == 1:
            rank = next(iter(rank_counts))
            return Combination(
                type=CombinationType.PAIR,
                cards=cards,
                rank=float(rank),
                length=1,
            )
        return None

    if len(rank_counts) == 1:
        rank, group = next(iter(rank_counts.items()))
        if len(group) == 2:
            return Combination(
                type=CombinationType.PAIR,
                cards=cards,
                rank=float(rank),
                length=1,
            )

    return None


def _detect_triple(
    rank_counts: dict[int, list[Card]],
    has_phoenix: bool,
    has_mah_jong: bool,
    cards: list[Card],
) -> Combination | None:
    if has_mah_jong:
        return None

    if has_phoenix:
        if len(rank_counts) == 1:
            rank, group = next(iter(rank_counts.items()))
            if len(group) == 2:
                return Combination(
                    type=CombinationType.TRIPLE,
                    cards=cards,
                    rank=float(rank),
                    length=1,
                )
        return None

    if len(rank_counts) == 1:
        rank, group = next(iter(rank_counts.items()))
        if len(group) == 3:
            return Combination(
                type=CombinationType.TRIPLE,
                cards=cards,
                rank=float(rank),
                length=1,
            )

    return None


def _detect_full_house(
    rank_counts: dict[int, list[Card]],
    has_phoenix: bool,
    has_mah_jong: bool,
    cards: list[Card],
) -> Combination | None:
    if has_mah_jong:
        return None

    counts = {r: len(g) for r, g in rank_counts.items()}

    if has_phoenix:
        if len(counts) == 2:
            sorted_ranks = sorted(counts.keys())
            count_vals = sorted(counts.values())

            # two pairs + phoenix: phoenix joins higher pair to form trio
            if count_vals == [2, 2]:
                trio_rank = sorted_ranks[1]
                return Combination(
                    type=CombinationType.FULL_HOUSE,
                    cards=cards,
                    rank=float(trio_rank),
                    length=5,
                )

            # trio + singleton + phoenix: phoenix pairs with singleton
            if count_vals == [1, 3]:
                trio_rank = [r for r, c in counts.items() if c == 3][0]
                return Combination(
                    type=CombinationType.FULL_HOUSE,
                    cards=cards,
                    rank=float(trio_rank),
                    length=5,
                )

    else:
        if len(counts) == 2:
            count_vals = sorted(counts.values())
            if count_vals == [2, 3]:
                trio_rank = [r for r, c in counts.items() if c == 3][0]
                return Combination(
                    type=CombinationType.FULL_HOUSE,
                    cards=cards,
                    rank=float(trio_rank),
                    length=5,
                )

    return None


def _detect_pair_sequence(
    rank_counts: dict[int, list[Card]],
    has_phoenix: bool,
    has_mah_jong: bool,
    cards: list[Card],
) -> Combination | None:
    if has_mah_jong:
        return None

    counts = {r: len(g) for r, g in rank_counts.items()}
    sorted_ranks = sorted(counts.keys())

    if not sorted_ranks:
        return None

    if has_phoenix:
        # all ranks must have count 1 or 2, exactly one rank has count 1
        ones = [r for r, c in counts.items() if c == 1]
        twos = [r for r, c in counts.items() if c == 2]
        if len(ones) != 1 or any(c > 2 for c in counts.values()):
            return None
        num_pairs = len(twos) + 1  # phoenix fills the missing card
        if num_pairs < MIN_PAIR_SEQUENCE_PAIRS:
            return None
        if not _is_consecutive(sorted_ranks):
            return None
        return Combination(
            type=CombinationType.PAIR_SEQUENCE,
            cards=cards,
            rank=float(sorted_ranks[-1]),
            length=num_pairs,
        )

    if any(c != 2 for c in counts.values()):
        return None
    num_pairs = len(sorted_ranks)
    if num_pairs < MIN_PAIR_SEQUENCE_PAIRS:
        return None
    if not _is_consecutive(sorted_ranks):
        return None

    return Combination(
        type=CombinationType.PAIR_SEQUENCE,
        cards=cards,
        rank=float(sorted_ranks[-1]),
        length=num_pairs,
    )


def _detect_straight(
    rank_counts: dict[int, list[Card]],
    has_phoenix: bool,
    has_mah_jong: bool,
    cards: list[Card],
) -> Combination | None:
    ranks_in_play: list[int] = []

    if has_mah_jong:
        ranks_in_play.append(1)

    for rank, group in rank_counts.items():
        if len(group) != 1:
            return None
        ranks_in_play.append(rank)

    ranks_in_play.sort()

    if has_phoenix:
        result = _fit_phoenix_in_straight(ranks_in_play)
        if result is None:
            return None
        high_rank, length = result
        if length < MIN_STRAIGHT_LENGTH:
            return None
        return Combination(
            type=CombinationType.STRAIGHT,
            cards=cards,
            rank=float(high_rank),
            length=length,
        )

    if len(ranks_in_play) < MIN_STRAIGHT_LENGTH:
        return None
    if not _is_consecutive(ranks_in_play):
        return None

    return Combination(
        type=CombinationType.STRAIGHT,
        cards=cards,
        rank=float(ranks_in_play[-1]),
        length=len(ranks_in_play),
    )


def _fit_phoenix_in_straight(ranks: list[int]) -> tuple[int, int] | None:
    """Find best placement for Phoenix in a straight. Returns (high_rank, length) or None."""
    if not ranks:
        return None

    sorted_ranks = sorted(ranks)
    n = len(sorted_ranks)

    if len(set(sorted_ranks)) != n:
        return None

    gaps = []
    for i in range(1, n):
        diff = sorted_ranks[i] - sorted_ranks[i - 1]
        if diff == 1:
            continue
        elif diff == 2:
            gaps.append(i)
        else:
            return None

    if len(gaps) == 0:
        # no gap: phoenix extends at top for highest rank
        high = sorted_ranks[-1] + 1
        if high > 14:
            high = sorted_ranks[-1]
            return (high, n + 1)  # extend at bottom instead
        return (high, n + 1)
    elif len(gaps) == 1:
        # phoenix fills the gap
        return (sorted_ranks[-1], n + 1)
    else:
        return None


def _is_consecutive(sorted_ranks: list[int]) -> bool:
    for i in range(1, len(sorted_ranks)):
        if sorted_ranks[i] - sorted_ranks[i - 1] != 1:
            return False
    return True
