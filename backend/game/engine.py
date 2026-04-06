from __future__ import annotations

from game.combinations import can_play_on, detect_combination
from game.constants import INITIAL_DEAL
from game.deck import create_deck, shuffle_deck
from game.models import (
    Card,
    Combination,
    CombinationType,
    GamePhase,
    GameState,
    Player,
    SpecialType,
)
from game.scoring import apply_tichu_bonuses, check_game_over, score_round
from game.wish import check_wish_obligation, clear_wish_if_fulfilled, set_wish


class EngineError(Exception):
    pass


class TichuEngine:

    @staticmethod
    def create_game(game_id: str, players_info: list[dict]) -> GameState:
        """Create a new game in WAITING phase.

        players_info: list of dicts with keys id, name.
        Seats are assigned 0-3 in order. Teams: seats 0,2 = team 0; seats 1,3 = team 1.
        """
        if len(players_info) != 4:
            raise EngineError("Exactly 4 players required")

        players = []
        for i, info in enumerate(players_info):
            players.append(Player(
                id=info["id"],
                name=info["name"],
                team=i % 2,
                seat=i,
            ))

        return GameState(
            id=game_id,
            phase=GamePhase.WAITING,
            players=players,
        )

    @staticmethod
    def start_round(state: GameState) -> None:
        """Begin a new round: shuffle, deal first 8 cards, enter GRAND_TICHU phase."""
        if state.phase not in (GamePhase.WAITING, GamePhase.ROUND_OVER):
            raise EngineError(f"Cannot start round in phase {state.phase}")

        deck = shuffle_deck(create_deck())
        state._dealt_deck = deck

        for i, player in enumerate(state.players):
            player.hand = deck[i * INITIAL_DEAL:(i + 1) * INITIAL_DEAL]
            player.tricks_won = []
            player.has_gone_out = False
            player.out_order = None
            player.has_played_card = False
            player.cards_to_push = {}
            player.has_pushed = False
            if player.called_tichu != "grand":
                player.called_tichu = None

        state.trick = []
        state.consecutive_passes = 0
        state.active_wish = None
        state.out_order = []
        state.leading_player_seat = None
        state.grand_tichu_decisions = {}
        state.pending_dragon_give = False
        state.dragon_player_seat = None
        state.pending_wish_from_seat = None
        state.phase = GamePhase.GRAND_TICHU

    @staticmethod
    def grand_tichu_decision(state: GameState, seat: int, call_grand: bool) -> None:
        if state.phase != GamePhase.GRAND_TICHU:
            raise EngineError("Not in grand tichu phase")
        if seat in state.grand_tichu_decisions:
            raise EngineError("Already decided")

        state.grand_tichu_decisions[seat] = call_grand
        if call_grand:
            state.players[seat].called_tichu = "grand"

        if len(state.grand_tichu_decisions) == 4:
            _deal_remaining(state)
            state.phase = GamePhase.PUSHING

    @staticmethod
    def push_cards(state: GameState, seat: int, cards_map: dict[int, Card]) -> None:
        """Player pushes one card to each other player.

        cards_map: {target_seat: Card} with exactly 3 entries (one per non-self player).
        """
        if state.phase != GamePhase.PUSHING:
            raise EngineError("Not in pushing phase")

        player = state.players[seat]
        if player.has_pushed:
            raise EngineError("Already pushed")

        if len(cards_map) != 3:
            raise EngineError("Must push exactly 3 cards (one to each other player)")

        for target_seat, card in cards_map.items():
            if target_seat == seat:
                raise EngineError("Cannot push card to self")
            if card not in player.hand:
                raise EngineError(f"Card {card} not in hand")

        player.cards_to_push = {str(s): c for s, c in cards_map.items()}
        player.has_pushed = True

        if all(p.has_pushed for p in state.players):
            _execute_push(state)
            _find_mah_jong_holder_and_set_turn(state)
            state.phase = GamePhase.PLAYING

    @staticmethod
    def play_cards(state: GameState, seat: int, cards: list[Card]) -> dict:
        """Play a combination of cards. Returns action result dict."""
        if state.phase != GamePhase.PLAYING:
            raise EngineError("Not in playing phase")
        if state.pending_dragon_give:
            raise EngineError("Must resolve dragon give first")
        if state.pending_wish_from_seat is not None:
            raise EngineError("Must make a wish first")

        player = state.players[seat]
        if player.has_gone_out:
            raise EngineError("Player already out")

        combo = detect_combination(cards)
        if combo is None:
            raise EngineError("Invalid combination")

        is_bomb = combo.is_bomb
        if not is_bomb and state.current_player_seat != seat:
            raise EngineError("Not your turn")

        current_trick_top = state.trick[-1][1] if state.trick else None

        if is_bomb and state.current_player_seat != seat:
            if not can_play_on(combo, current_trick_top):
                raise EngineError("Bomb does not beat current trick")
        else:
            if current_trick_top is not None:
                if combo.type == CombinationType.HOUND_LEAD:
                    raise EngineError("Hound can only be played as a lead")
                if not can_play_on(combo, current_trick_top):
                    raise EngineError("Combination does not beat current trick")

            if state.active_wish is not None and not is_bomb:
                if check_wish_obligation(state, seat):
                    has_wished_card = any(
                        c.special is None and c.rank == state.active_wish
                        for c in cards
                    )
                    if not has_wished_card:
                        raise EngineError(
                            f"Must play wished rank {state.active_wish} if possible"
                        )

        for card in cards:
            if card not in player.hand:
                raise EngineError(f"Card {card} not in hand")
            player.hand.remove(card)

        player.has_played_card = True

        if combo.type == CombinationType.HOUND_LEAD:
            return _handle_hound_lead(state, seat, combo)

        state.trick.append((seat, combo))
        state.consecutive_passes = 0

        if not state.trick[:-1]:
            state.leading_player_seat = seat

        if is_bomb and state.current_player_seat != seat:
            state.leading_player_seat = seat

        clear_wish_if_fulfilled(state, cards)

        result = {"action": "play", "seat": seat, "combination": combo}

        has_mah_jong = any(c.special == SpecialType.MAH_JONG for c in cards)
        if has_mah_jong and state.active_wish is None:
            state.pending_wish_from_seat = seat
            result["needs_wish"] = True

        if not player.hand:
            _handle_player_out(state, seat)
            result["went_out"] = True
            if _check_round_end(state):
                _end_round(state)
                result["round_over"] = True
                return result

        _advance_turn(state, seat)
        return result

    @staticmethod
    def pass_turn(state: GameState, seat: int) -> dict:
        if state.phase != GamePhase.PLAYING:
            raise EngineError("Not in playing phase")
        if state.current_player_seat != seat:
            raise EngineError("Not your turn")
        if state.pending_dragon_give:
            raise EngineError("Must resolve dragon give first")

        player = state.players[seat]
        if player.has_gone_out:
            raise EngineError("Player already out")

        if not state.trick:
            raise EngineError("Cannot pass on empty trick (must lead)")

        state.consecutive_passes += 1
        result = {"action": "pass", "seat": seat}

        active_count = sum(1 for p in state.players if not p.has_gone_out)
        passes_needed = active_count - 1

        if state.consecutive_passes >= passes_needed:
            winner_seat = state.trick[-1][0]

            trick_has_dragon = any(
                c.special == SpecialType.DRAGON
                for _, combo in state.trick
                for c in combo.cards
            )

            if trick_has_dragon:
                dragon_seat = None
                for s, combo in state.trick:
                    if any(c.special == SpecialType.DRAGON for c in combo.cards):
                        dragon_seat = s
                        break
                if dragon_seat == winner_seat:
                    state.pending_dragon_give = True
                    state.dragon_player_seat = winner_seat
                    state.current_player_seat = winner_seat
                    result["needs_dragon_give"] = True
                    return result

            _collect_trick(state, winner_seat)
            result["trick_won"] = winner_seat

            if _check_round_end(state):
                _end_round(state)
                result["round_over"] = True
                return result

            if state.players[winner_seat].has_gone_out:
                next_seat = _next_active_seat(state, winner_seat)
                state.current_player_seat = next_seat
                state.leading_player_seat = next_seat
            else:
                state.current_player_seat = winner_seat
                state.leading_player_seat = winner_seat
        else:
            _advance_turn(state, seat)

        return result

    @staticmethod
    def call_small_tichu(state: GameState, seat: int) -> None:
        if state.phase != GamePhase.PLAYING:
            raise EngineError("Not in playing phase")

        player = state.players[seat]
        if player.has_played_card:
            raise EngineError("Cannot call small tichu after playing a card")
        if player.called_tichu is not None:
            raise EngineError("Already called tichu")

        player.called_tichu = "small"

    @staticmethod
    def make_wish(state: GameState, seat: int, rank: int) -> None:
        if state.pending_wish_from_seat != seat:
            raise EngineError("Not expecting a wish from this player")
        set_wish(state, rank)

    @staticmethod
    def skip_wish(state: GameState, seat: int) -> None:
        if state.pending_wish_from_seat != seat:
            raise EngineError("Not expecting a wish from this player")
        state.pending_wish_from_seat = None

    @staticmethod
    def dragon_give(state: GameState, seat: int, opponent_seat: int) -> dict:
        if not state.pending_dragon_give:
            raise EngineError("No pending dragon give")
        if state.dragon_player_seat != seat:
            raise EngineError("Not the dragon player")

        opponent = state.players[opponent_seat]
        if opponent.team == state.players[seat].team:
            raise EngineError("Must give dragon trick to an opponent")

        trick_cards = []
        for _, combo in state.trick:
            trick_cards.extend(combo.cards)
        opponent.tricks_won.append(trick_cards)

        state.trick = []
        state.consecutive_passes = 0
        state.pending_dragon_give = False
        state.dragon_player_seat = None

        result = {"action": "dragon_give", "seat": seat, "recipient": opponent_seat}

        if _check_round_end(state):
            _end_round(state)
            result["round_over"] = True
            return result

        if state.players[seat].has_gone_out:
            next_seat = _next_active_seat(state, seat)
            state.current_player_seat = next_seat
            state.leading_player_seat = next_seat
        else:
            state.current_player_seat = seat
            state.leading_player_seat = seat

        return result


def _deal_remaining(state: GameState) -> None:
    deck = state._dealt_deck
    remaining_start = INITIAL_DEAL * 4
    remaining = deck[remaining_start:]
    per_player = len(remaining) // 4
    for i, player in enumerate(state.players):
        player.hand.extend(remaining[i * per_player:(i + 1) * per_player])
        player.hand.sort(key=lambda c: c.sort_key)


def _execute_push(state: GameState) -> None:
    received: dict[int, list[Card]] = {i: [] for i in range(4)}

    for player in state.players:
        for target_seat_str, card in player.cards_to_push.items():
            target_seat = int(target_seat_str)
            player.hand.remove(card)
            received[target_seat].append(card)

    for seat, cards in received.items():
        state.players[seat].hand.extend(cards)
        state.players[seat].hand.sort(key=lambda c: c.sort_key)


def _find_mah_jong_holder_and_set_turn(state: GameState) -> None:
    for player in state.players:
        for card in player.hand:
            if card.special == SpecialType.MAH_JONG:
                state.current_player_seat = player.seat
                state.leading_player_seat = player.seat
                return


def _handle_hound_lead(state: GameState, seat: int, combo: Combination) -> dict:
    partner_seat = (seat + 2) % 4
    if state.players[partner_seat].has_gone_out:
        target = _next_active_seat(state, partner_seat)
    else:
        target = partner_seat

    state.current_player_seat = target
    state.leading_player_seat = target
    state.trick = []
    state.consecutive_passes = 0
    return {"action": "hound_lead", "seat": seat, "transfer_to": target}


def _handle_player_out(state: GameState, seat: int) -> None:
    player = state.players[seat]
    player.has_gone_out = True
    player.out_order = len(state.out_order) + 1
    state.out_order.append(seat)


def _check_round_end(state: GameState) -> bool:
    out_count = sum(1 for p in state.players if p.has_gone_out)
    if out_count >= 3:
        return True
    if len(state.out_order) >= 2:
        first = state.players[state.out_order[0]]
        second = state.players[state.out_order[1]]
        if first.team == second.team:
            return True
    return False


def _collect_trick(state: GameState, winner_seat: int) -> None:
    trick_cards = []
    for _, combo in state.trick:
        trick_cards.extend(combo.cards)
    state.players[winner_seat].tricks_won.append(trick_cards)
    state.trick = []
    state.consecutive_passes = 0


def _advance_turn(state: GameState, from_seat: int) -> None:
    next_seat = _next_active_seat(state, from_seat)
    state.current_player_seat = next_seat


def _next_active_seat(state: GameState, after_seat: int) -> int:
    for i in range(1, 5):
        candidate = (after_seat + i) % 4
        if not state.players[candidate].has_gone_out:
            return candidate
    raise EngineError("No active players remaining")


def _end_round(state: GameState) -> None:
    round_scores = score_round(state)
    final_scores = apply_tichu_bonuses(state, round_scores)
    state.scores[0] += final_scores[0]
    state.scores[1] += final_scores[1]

    winner = check_game_over(state.scores)
    if winner is not None:
        state.phase = GamePhase.GAME_OVER
    else:
        state.phase = GamePhase.ROUND_OVER
        state.round_number += 1
