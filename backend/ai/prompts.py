from __future__ import annotations

from game.models import Card, GamePhase, GameState
from ws.broadcaster import _get_valid_actions

SYSTEM_PROMPT = """\
You are an AI playing the card game Tichu. Respond with ONLY a JSON object, no other text.

## Card Representation
Each card is a JSON object with: suit, rank, special.
Suits: "jade", "sword", "pagoda", "star", "special"
Ranks: 2-14 (11=J, 12=Q, 13=K, 14=A), or null for special cards.
Special types: "dragon", "phoenix", "hound", "mah_jong", or null for normal cards.

## Combination Types
- single: 1 card
- pair: 2 cards of same rank (phoenix can substitute)
- triple: 3 cards of same rank (phoenix can substitute)
- full_house: 3 of a kind + pair (5 cards, phoenix can substitute)
- pair_sequence: 2+ consecutive pairs (phoenix can fill one gap)
- straight: 5+ consecutive ranks (phoenix can fill one gap, mah_jong counts as rank 1)
- four_bomb: 4 cards of same rank (no phoenix)
- straight_bomb: 5+ consecutive same suit (no phoenix)
- hound_lead: play the hound as a single to transfer lead to partner

## Actions
Respond with a JSON object. The "action" field must be one of your valid_actions.

### grand_tichu_decision
{"action": "grand_tichu_decision", "call": true/false}
Call grand tichu only with an exceptional hand (multiple bombs, dragon + phoenix + strong suits).

### push_cards
{"action": "push_cards", "cards": {"<seat>": <card>, "<seat>": <card>, "<seat>": <card>}}
Push exactly 3 cards, one to each other player (keyed by their seat number as a string).
Push weak cards to opponents and strong cards to your partner.
Your partner sits 2 seats away (your_seat + 2) % 4.

### play_cards
{"action": "play_cards", "cards": [<card>, ...]}
Play a valid combination that beats the current trick (if any).
When leading (no trick on table), play any valid combination.

### pass_turn
{"action": "pass_turn"}
Pass when you cannot or choose not to beat the current trick.

### call_small_tichu
{"action": "call_small_tichu"}
Call only if you have a very strong hand and have not played any card yet.

### make_wish
{"action": "make_wish", "rank": <2-14>}
Wish for a rank (2-14) after playing the Mah Jong. Wish for a rank opponents likely hold.

### skip_wish
{"action": "skip_wish"}

### dragon_give
{"action": "dragon_give", "opponent_seat": <seat>}
Give the dragon trick to an opponent. Must be a player on the other team.

## Strategy Tips
- Play low singles and pairs early to get rid of weak cards.
- Keep bombs for disrupting opponents about to go out.
- Lead with your strongest suit sequences.
- Track which cards have been played.
- Coordinate with your partner (same team = seats 0,2 or seats 1,3).
- Dragon is the highest single (rank 15) worth 25 points.
- Phoenix is a wild card worth -25 points; as a single it is rank 0.5 above the current trick.
- Hound transfers lead to partner, only playable as a lead.
"""


def format_game_state_for_ai(state: GameState, seat: int) -> str:
    player = state.players[seat]
    partner_seat = (seat + 2) % 4
    opponent_seats = [s for s in range(4) if s != seat and s != partner_seat]

    hand_str = _format_cards(player.hand)
    valid_actions = _get_valid_actions(state, seat)

    lines = [
        f"Your seat: {seat}",
        f"Your team: {player.team} (partner at seat {partner_seat})",
        f"Opponents: seats {opponent_seats}",
        f"Phase: {state.phase.value}",
        f"Scores: team 0 = {state.scores[0]}, team 1 = {state.scores[1]}",
        f"Round: {state.round_number}",
        f"Your hand ({len(player.hand)} cards): {hand_str}",
        f"Valid actions: {valid_actions}",
    ]

    if state.phase == GamePhase.GRAND_TICHU:
        lines.append("You have only seen your first 8 cards. Decide on grand tichu.")

    if state.phase == GamePhase.PUSHING:
        other_seats = [s for s in range(4) if s != seat]
        lines.append(f"Push one card to each of these seats: {other_seats}")

    if state.phase == GamePhase.PLAYING:
        lines.append(f"Current player seat: {state.current_player_seat}")

        if state.trick:
            trick_parts = []
            for s, combo in state.trick:
                trick_parts.append(
                    f"  seat {s}: {combo.type.value} rank={combo.rank} "
                    f"cards={_format_cards(combo.cards)}"
                )
            lines.append("Current trick:\n" + "\n".join(trick_parts))
        else:
            lines.append("No trick on table (you lead).")

        if state.active_wish is not None:
            lines.append(f"Active wish for rank: {state.active_wish}")

        if state.pending_dragon_give and state.dragon_player_seat == seat:
            lines.append(
                f"You must give the dragon trick to an opponent: "
                f"seats {opponent_seats}"
            )

        if state.pending_wish_from_seat == seat:
            lines.append(
                "You played the Mah Jong. Choose a rank to wish for (2-14) or skip."
            )

        for p in state.players:
            if p.seat == seat:
                continue
            status = "OUT" if p.has_gone_out else f"{len(p.hand)} cards"
            tichu = f", called {p.called_tichu}" if p.called_tichu else ""
            lines.append(f"  Player seat {p.seat} ({p.name}): {status}{tichu}")

        if state.out_order:
            lines.append(f"Out order: {state.out_order}")

    return "\n".join(lines)


def _format_cards(cards: list[Card]) -> str:
    parts = []
    for c in cards:
        if c.special:
            parts.append(
                f'{{"suit":"{c.suit.value}","rank":null,"special":"{c.special.value}"}}'
            )
        else:
            parts.append(f'{{"suit":"{c.suit.value}","rank":{c.rank},"special":null}}')
    return "[" + ",".join(parts) + "]"
