from __future__ import annotations

import json
import logging

from ai.client import get_client
from ai.prompts import SYSTEM_PROMPT, format_game_state_for_ai
from game.combinations import can_play_on, detect_combination
from game.engine import TichuEngine
from game.models import Card, GameState
from game.wish import check_wish_obligation
from ws.broadcaster import _get_valid_actions

logger = logging.getLogger(__name__)

AI_MODEL = "claude-haiku-4-5-20251001"


async def ai_decide(state: GameState, seat: int) -> dict | None:
    """Make a decision for the AI player at the given seat.

    Returns the action result dict from the engine call, or None if the
    action produced no result (e.g. grand tichu decision before all players
    have decided).
    """
    valid_actions = _get_valid_actions(state, seat)
    if not valid_actions:
        return None

    user_message = format_game_state_for_ai(state, seat)
    decision = await _call_llm(user_message)

    if decision is not None:
        action = decision.get("action")
        if action in valid_actions:
            try:
                return _execute_action(state, seat, decision, valid_actions)
            except Exception:
                logger.exception(
                    "AI decision execution failed for seat %d, using fallback", seat
                )

    return _execute_fallback(state, seat, valid_actions)


def _extract_json(text: str) -> dict | None:
    """Extract the first JSON object from text that may contain extra content."""
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None

    return None


async def _call_llm(user_message: str) -> dict | None:
    try:
        client = get_client()
        response = await client.messages.create(
            model=AI_MODEL,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        text = response.content[0].text.strip()
        result = _extract_json(text)
        if result is None:
            logger.warning("Could not extract JSON from LLM response: %s", text[:200])
        return result
    except Exception:
        logger.exception("LLM call failed")
        return None


def _execute_action(
    state: GameState, seat: int, decision: dict, valid_actions: list[str]
) -> dict | None:
    action = decision["action"]

    if action == "grand_tichu_decision":
        TichuEngine.grand_tichu_decision(state, seat, bool(decision.get("call", False)))
        return None

    if action == "push_cards":
        raw_map = decision.get("cards", {})
        cards_map: dict[int, Card] = {}
        for target_seat_str, card_data in raw_map.items():
            cards_map[int(target_seat_str)] = Card(**card_data)
        TichuEngine.push_cards(state, seat, cards_map)
        return None

    if action == "play_cards":
        cards = [Card(**c) for c in decision.get("cards", [])]
        return TichuEngine.play_cards(state, seat, cards)

    if action == "pass_turn":
        return TichuEngine.pass_turn(state, seat)

    if action == "call_small_tichu":
        TichuEngine.call_small_tichu(state, seat)
        return None

    if action == "make_wish":
        rank = decision.get("rank", 8)
        TichuEngine.make_wish(state, seat, rank)
        return None

    if action == "skip_wish":
        TichuEngine.skip_wish(state, seat)
        return None

    if action == "dragon_give":
        opponent_seat = decision.get("opponent_seat")
        return TichuEngine.dragon_give(state, seat, opponent_seat)

    return None


def _execute_fallback(
    state: GameState, seat: int, valid_actions: list[str]
) -> dict | None:
    logger.info("Using fallback for seat %d, valid_actions=%s", seat, valid_actions)

    if "grand_tichu_decision" in valid_actions:
        TichuEngine.grand_tichu_decision(state, seat, False)
        return None

    if "push_cards" in valid_actions:
        return _fallback_push(state, seat)

    if "make_wish" in valid_actions or "skip_wish" in valid_actions:
        TichuEngine.skip_wish(state, seat)
        return None

    if "dragon_give" in valid_actions:
        return _fallback_dragon_give(state, seat)

    if state.pending_wish_from_seat is not None or state.pending_dragon_give:
        return None

    if "play_cards" in valid_actions:
        result = _fallback_play(state, seat)
        if result is not None:
            return result

    if "pass" in valid_actions:
        return TichuEngine.pass_turn(state, seat)

    if "play_cards" in valid_actions:
        return _fallback_play_any(state, seat)

    return None


def _fallback_push(state: GameState, seat: int) -> None:
    player = state.players[seat]
    sorted_hand = sorted(player.hand, key=lambda c: c.sort_key)

    other_seats = [s for s in range(4) if s != seat]
    cards_map: dict[int, Card] = {}
    for i, target in enumerate(other_seats):
        cards_map[target] = sorted_hand[i]

    TichuEngine.push_cards(state, seat, cards_map)
    return None


def _fallback_dragon_give(state: GameState, seat: int) -> dict:
    player_team = state.players[seat].team
    opponents = [p for p in state.players if p.team != player_team]
    opponents.sort(
        key=lambda p: sum(c.point_value for trick in p.tricks_won for c in trick)
    )
    return TichuEngine.dragon_give(state, seat, opponents[0].seat)


def _fallback_play(state: GameState, seat: int) -> dict | None:
    """Try to play the lowest valid combination, respecting wish obligation."""
    player = state.players[seat]
    current_trick_top = state.trick[-1][1] if state.trick else None

    if state.active_wish is not None and check_wish_obligation(state, seat):
        wished_cards = [
            c for c in player.hand if c.special is None and c.rank == state.active_wish
        ]
        if wished_cards:
            combo = detect_combination(wished_cards[:1])
            if combo and can_play_on(combo, current_trick_top):
                return TichuEngine.play_cards(state, seat, wished_cards[:1])

    sorted_hand = sorted(player.hand, key=lambda c: c.sort_key)

    for card in sorted_hand:
        combo = detect_combination([card])
        if combo and can_play_on(combo, current_trick_top):
            try:
                return TichuEngine.play_cards(state, seat, [card])
            except Exception:
                continue

    return None


def _fallback_play_any(state: GameState, seat: int) -> dict | None:
    """When leading, play the lowest single card."""
    player = state.players[seat]
    if not player.hand:
        return None
    sorted_hand = sorted(player.hand, key=lambda c: c.sort_key)
    for card in sorted_hand:
        combo = detect_combination([card])
        if combo:
            try:
                return TichuEngine.play_cards(state, seat, [card])
            except Exception:
                continue
    return None
