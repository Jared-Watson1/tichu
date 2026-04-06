from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict

from game.constants import DRAGON_POINTS, PHOENIX_POINTS, POINT_VALUES, RANK_NAMES


class Suit(str, Enum):
    JADE = "jade"
    SWORD = "sword"
    PAGODA = "pagoda"
    STAR = "star"
    SPECIAL = "special"


class SpecialType(str, Enum):
    DRAGON = "dragon"
    PHOENIX = "phoenix"
    HOUND = "hound"
    MAH_JONG = "mah_jong"


class Card(BaseModel):
    model_config = ConfigDict(frozen=True)

    suit: Suit
    rank: int | None = None
    special: SpecialType | None = None

    @property
    def is_special(self) -> bool:
        return self.special is not None

    @property
    def display_rank(self) -> str:
        if self.special:
            return self.special.value
        return RANK_NAMES.get(self.rank, str(self.rank))

    @property
    def sort_key(self) -> float:
        if self.special == SpecialType.HOUND:
            return 0.5
        if self.special == SpecialType.MAH_JONG:
            return 1.0
        if self.special == SpecialType.PHOENIX:
            return 14.5
        if self.special == SpecialType.DRAGON:
            return 15.0
        return float(self.rank)

    @property
    def point_value(self) -> int:
        if self.special == SpecialType.DRAGON:
            return DRAGON_POINTS
        if self.special == SpecialType.PHOENIX:
            return PHOENIX_POINTS
        if self.rank in POINT_VALUES:
            return POINT_VALUES[self.rank]
        return 0


class CombinationType(str, Enum):
    SINGLE = "single"
    PAIR = "pair"
    PAIR_SEQUENCE = "pair_sequence"
    TRIPLE = "triple"
    FULL_HOUSE = "full_house"
    STRAIGHT = "straight"
    FOUR_BOMB = "four_bomb"
    STRAIGHT_BOMB = "straight_bomb"
    HOUND_LEAD = "hound_lead"


class Combination(BaseModel):
    type: CombinationType
    cards: list[Card]
    rank: float
    length: int
    is_bomb: bool = False

    def beats(self, other: Combination) -> bool:
        if self.is_bomb and not other.is_bomb:
            return True
        if not self.is_bomb and other.is_bomb:
            return False
        if self.is_bomb and other.is_bomb:
            if self.length != other.length:
                return self.length > other.length
            return self.rank > other.rank
        if self.type != other.type:
            return False
        if self.length != other.length:
            return False
        return self.rank > other.rank


class GamePhase(str, Enum):
    WAITING = "waiting"
    DEALING = "dealing"
    GRAND_TICHU = "grand_tichu"
    PUSHING = "pushing"
    PLAYING = "playing"
    ROUND_OVER = "round_over"
    GAME_OVER = "game_over"


class Player(BaseModel):
    model_config = ConfigDict(frozen=False)

    id: str
    name: str
    team: int
    seat: int
    hand: list[Card] = []
    tricks_won: list[list[Card]] = []
    has_gone_out: bool = False
    out_order: int | None = None
    called_tichu: str | None = None
    has_played_card: bool = False
    cards_to_push: dict[str, Card] = {}
    has_pushed: bool = False


class GameState(BaseModel):
    model_config = ConfigDict(frozen=False)

    id: str
    phase: GamePhase
    players: list[Player]
    current_player_seat: int = 0
    trick: list[tuple[int, Combination]] = []
    consecutive_passes: int = 0
    active_wish: int | None = None
    out_order: list[int] = []
    scores: list[int] = [0, 0]
    round_number: int = 1
    leading_player_seat: int | None = None
    grand_tichu_decisions: dict[int, bool] = {}
    pending_dragon_give: bool = False
    dragon_player_seat: int | None = None
    pending_wish_from_seat: int | None = None
    _dealt_deck: list[Card] = []
