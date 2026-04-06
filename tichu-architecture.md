# Tichu Online — Architecture & Build Plan

## Overview

A real-time multiplayer implementation of Tichu Nanking (4-player) with a React (Vite) frontend and Python FastAPI backend. Players create/join games via lobby, then play full Tichu hands with WebSocket-driven state sync.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | React 18 + Vite + TypeScript | Fast dev, strong typing for complex game state |
| Styling | Tailwind CSS | Rapid UI iteration |
| Real-time (client) | Native WebSocket | No library overhead needed for this scale |
| Backend | Python FastAPI | Native async, WebSocket support, Pydantic models |
| Real-time (server) | FastAPI WebSockets | Built-in, no extra deps |
| State management | In-memory (server-side) | MVP — no DB needed yet |
| Client state | Zustand | Lightweight, perfect for game state |
| Deployment | Docker Compose | Single command local dev, easy deploy |

---

## Project Structure

```
tichu/
├── docker-compose.yml
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── main.py                    # FastAPI app entry, CORS, lifespan
│   │
│   ├── game/
│   │   ├── __init__.py
│   │   ├── models.py              # Pydantic models (Card, Player, GameState, etc.)
│   │   ├── constants.py           # Card ranks, suits, special cards, scoring values
│   │   ├── deck.py                # Deck creation, shuffling, dealing
│   │   ├── combinations.py        # Combination detection & validation
│   │   ├── engine.py              # Core game logic state machine
│   │   ├── scoring.py             # Hand scoring, tichu bonuses, game-end checks
│   │   └── wish.py                # Mah Jong wish tracking & enforcement
│   │
│   ├── lobby/
│   │   ├── __init__.py
│   │   ├── manager.py             # Game creation, joining, room management
│   │   └── models.py              # Lobby-specific models
│   │
│   ├── ws/
│   │   ├── __init__.py
│   │   ├── handler.py             # WebSocket connection lifecycle
│   │   ├── protocol.py            # Message types & serialization
│   │   └── broadcaster.py         # Selective state broadcasting
│   │
│   └── tests/
│       ├── test_combinations.py
│       ├── test_engine.py
│       ├── test_scoring.py
│       └── test_wish.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   │
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   │
│   │   ├── stores/
│   │   │   ├── gameStore.ts       # Zustand store for game state
│   │   │   └── lobbyStore.ts      # Zustand store for lobby state
│   │   │
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts    # WebSocket connection & reconnection
│   │   │   └── useGameActions.ts  # Action dispatchers (play, pass, tichu, etc.)
│   │   │
│   │   ├── components/
│   │   │   ├── Lobby/
│   │   │   │   ├── CreateGame.tsx
│   │   │   │   ├── JoinGame.tsx
│   │   │   │   └── WaitingRoom.tsx
│   │   │   │
│   │   │   ├── Game/
│   │   │   │   ├── GameBoard.tsx       # Main game layout (4 positions)
│   │   │   │   ├── PlayerHand.tsx      # Current player's cards (interactive)
│   │   │   │   ├── OpponentHand.tsx    # Other players (card backs + count)
│   │   │   │   ├── TrickArea.tsx       # Center area showing current trick
│   │   │   │   ├── CardPush.tsx        # Card exchange UI (pre-hand)
│   │   │   │   ├── ScoreBoard.tsx      # Running team scores
│   │   │   │   ├── ActionBar.tsx       # Play, Pass, Tichu buttons
│   │   │   │   ├── WishIndicator.tsx   # Active Mah Jong wish display
│   │   │   │   └── GameLog.tsx         # Action history feed
│   │   │   │
│   │   │   └── Card/
│   │   │       ├── Card.tsx            # Individual card render
│   │   │       └── CardStack.tsx       # Fan/stack layouts
│   │   │
│   │   ├── types/
│   │   │   ├── game.ts            # TypeScript types mirroring backend models
│   │   │   └── ws.ts              # WebSocket message types
│   │   │
│   │   └── utils/
│   │       ├── cardUtils.ts       # Card sorting, grouping helpers
│   │       └── combinationUtils.ts # Client-side combination detection (for UI hints)
│   │
│   └── public/
│       └── cards/                 # Card artwork (SVG or PNG)
```

---

## Data Models (Backend — Pydantic)

### Card

```python
from enum import Enum
from pydantic import BaseModel

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
    suit: Suit
    rank: int | None = None          # 2-14 (J=11, Q=12, K=13, A=14), None for specials
    special: SpecialType | None = None

    @property
    def is_special(self) -> bool:
        return self.special is not None

    @property
    def display_rank(self) -> str:
        if self.special:
            return self.special.value
        rank_names = {11: "J", 12: "Q", 13: "K", 14: "A"}
        return rank_names.get(self.rank, str(self.rank))

    @property
    def sort_key(self) -> float:
        """For hand sorting. Mah Jong=1, normal=2-14, Phoenix=14.5, Dragon=15"""
        if self.special == SpecialType.MAH_JONG:
            return 1.0
        if self.special == SpecialType.HOUND:
            return 0.5  # sort to front
        if self.special == SpecialType.PHOENIX:
            return 14.5
        if self.special == SpecialType.DRAGON:
            return 15.0
        return float(self.rank)

    @property
    def point_value(self) -> int:
        if self.special == SpecialType.DRAGON:
            return 25
        if self.special == SpecialType.PHOENIX:
            return -25
        if self.rank == 5:
            return 5
        if self.rank in (10, 13):  # 10 and King
            return 10
        return 0
```

### Combination Types

```python
class CombinationType(str, Enum):
    SINGLE = "single"
    PAIR = "pair"
    PAIR_SEQUENCE = "pair_sequence"   # consecutive pairs (at least 2 pairs)
    TRIPLE = "triple"
    FULL_HOUSE = "full_house"
    STRAIGHT = "straight"            # at least 5 consecutive
    FOUR_BOMB = "four_bomb"
    STRAIGHT_BOMB = "straight_bomb"  # 5+ same suit consecutive
    HOUND_LEAD = "hound_lead"        # special: hound played as lead

class Combination(BaseModel):
    type: CombinationType
    cards: list[Card]
    rank: float                      # primary comparison value
    length: int                      # for sequences/pair sequences
    is_bomb: bool = False

    def beats(self, other: "Combination") -> bool:
        """Can this combination beat the other?"""
        # Bombs beat everything non-bomb
        if self.is_bomb and not other.is_bomb:
            return True
        if not self.is_bomb and other.is_bomb:
            return False
        # Both bombs: compare by length first, then rank
        if self.is_bomb and other.is_bomb:
            if self.length != other.length:
                return self.length > other.length
            return self.rank > other.rank
        # Same type and length required
        if self.type != other.type:
            return False
        if self.length != other.length:
            return False
        return self.rank > other.rank
```

### Game State

```python
class GamePhase(str, Enum):
    WAITING = "waiting"              # lobby, waiting for players
    DEALING = "dealing"              # cards being distributed
    GRAND_TICHU = "grand_tichu"      # players deciding on grand tichu (first 8 cards)
    PUSHING = "pushing"              # exchanging 3 cards
    PLAYING = "playing"              # main gameplay
    ROUND_OVER = "round_over"        # scoring
    GAME_OVER = "game_over"          # team hit 1000+

class Player(BaseModel):
    id: str                          # unique session ID
    name: str
    team: int                        # 0 or 1
    seat: int                        # 0-3 (partners at 0,2 and 1,3)
    hand: list[Card] = []
    tricks_won: list[list[Card]] = []
    has_gone_out: bool = False
    out_order: int | None = None     # 1st, 2nd, 3rd, 4th
    called_tichu: str | None = None  # "small" | "grand" | None
    has_played_card: bool = False     # tracks if small tichu window is still open
    cards_to_push: dict[str, Card] = {}  # player_id -> card to push
    has_pushed: bool = False

class GameState(BaseModel):
    id: str                          # game room ID
    phase: GamePhase
    players: list[Player]            # always length 4
    current_player_seat: int         # whose turn it is (0-3)
    trick: list[tuple[int, Combination]] = []  # (seat, combination) pairs in current trick
    consecutive_passes: int = 0
    active_wish: int | None = None   # rank wished for via Mah Jong (2-14), None if no wish
    out_order: list[int] = []        # seats in order they went out
    scores: list[int] = [0, 0]       # team scores [team0, team1]
    round_number: int = 1
    leading_player_seat: int | None = None  # who led the current trick

    # Grand tichu phase tracking
    grand_tichu_decisions: dict[int, bool] = {}  # seat -> decided (True/False)
```

---

## WebSocket Protocol

All messages are JSON with a `type` field. The server sends different views to each player (hiding opponents' hands).

### Client → Server Messages

```typescript
// Lobby
{ type: "create_game", payload: { player_name: string } }
{ type: "join_game", payload: { game_id: string, player_name: string } }

// Grand Tichu phase
{ type: "grand_tichu_decision", payload: { call: boolean } }

// Card pushing phase
{ type: "push_cards", payload: { cards: { [player_id: string]: Card } } }

// Gameplay
{ type: "play_cards", payload: { cards: Card[] } }
{ type: "pass" }
{ type: "call_small_tichu" }
{ type: "make_wish", payload: { rank: number } }         // 2-14
{ type: "dragon_give", payload: { opponent_seat: number } }  // which opponent gets the trick

// Bombs (can be sent out of turn)
{ type: "play_bomb", payload: { cards: Card[] } }
```

### Server → Client Messages

```typescript
// Lobby
{ type: "game_created", payload: { game_id: string } }
{ type: "player_joined", payload: { player_name: string, seat: number, team: number } }
{ type: "game_starting" }

// Game state (sent after every action — tailored per player)
{ type: "game_state", payload: {
    phase: GamePhase,
    your_hand: Card[],
    your_seat: number,
    players: PlayerPublicInfo[],    // name, seat, team, card_count, has_gone_out, called_tichu
    current_player_seat: number,
    trick: TrickEntry[],            // { seat, combination } for current trick
    active_wish: number | null,
    scores: [number, number],
    round_number: number,
    consecutive_passes: number,
    out_order: number[],
    can_play: boolean,              // is it your turn (or can you bomb)?
    valid_actions: string[],        // ["play", "pass", "call_small_tichu", "bomb"]
}}

// Events
{ type: "cards_played", payload: { seat: number, combination: Combination } }
{ type: "player_passed", payload: { seat: number } }
{ type: "trick_won", payload: { seat: number } }
{ type: "tichu_called", payload: { seat: number, tichu_type: "small" | "grand" } }
{ type: "wish_made", payload: { rank: number } }
{ type: "wish_fulfilled" }
{ type: "player_out", payload: { seat: number, position: number } }
{ type: "round_over", payload: { round_scores: [number, number], total_scores: [number, number] } }
{ type: "game_over", payload: { winning_team: number, final_scores: [number, number] } }

// Errors
{ type: "error", payload: { message: string, code: string } }
```

---

## Game Engine — State Machine

```
  WAITING
     │
     ▼  (4 players joined)
  DEALING
     │
     ▼  (first 8 cards dealt)
  GRAND_TICHU ──── players decide yes/no on grand tichu
     │
     ▼  (all decided, remaining 6 cards dealt)
  PUSHING ──────── each player selects 3 cards to push
     │
     ▼  (all pushed, cards exchanged)
  PLAYING ──────── main game loop
     │  │
     │  ├── play_cards → validate combination → update trick → check out → next turn
     │  ├── pass → increment pass count → if 3 passes, trick won → new lead
     │  ├── bomb (out of turn) → interrupt → validate bomb → update trick
     │  ├── call_small_tichu → validate window → flag player
     │  ├── make_wish → set active_wish
     │  └── dragon_give → give trick to chosen opponent
     │
     ▼  (3 players out OR double victory)
  ROUND_OVER
     │
     ├── score < 1000 both teams → back to DEALING
     │
     ▼  (team hits 1000+)
  GAME_OVER
```

### Key Engine Rules to Implement

**Combination Validation (`combinations.py`):**
1. Parse a set of cards into a `Combination` — detect type automatically
2. Phoenix substitution: try all possible ranks it could represent
3. Bomb detection: four-of-a-kind or 5+ same-suit straight
4. Full house comparison uses trio rank only
5. Straights must be 5+ cards; Mah Jong counts as rank 1

**Wish Enforcement (`wish.py`):**
1. When Mah Jong is played, player may wish for rank 2-14
2. Wish persists until fulfilled
3. On each player's turn, check: does player hold a card of wished rank AND can they legally play it?
4. "Can legally play" means: as a single, in a pair, in a valid combination matching the current trick type
5. Phoenix does NOT count as the wished rank
6. Wish does NOT apply to out-of-turn bombs
7. If player wins trick with a bomb and must lead, wish applies to the new lead

**Dragon Trick Resolution:**
1. When Dragon wins a trick (3 passes after Dragon was played as single)
2. Prompt the Dragon's holder to choose which opponent receives the trick
3. The trick (including Dragon's 25 points) goes to the chosen opponent

**Turn Management:**
1. Normal flow: right to left (counter-clockwise), skipping players who went out
2. After trick won: winner leads (if out, pass right to next active player)
3. Hound lead: transfers lead to partner (if partner out, pass right)
4. Bomb interrupt: any active player can bomb at any time

**Round End & Scoring (`scoring.py`):**
1. Round ends when 3 of 4 players are out
2. Tailender gives remaining hand cards to opponents, tricks to the winner (1st out)
3. Point cards: King=10, Ten=10, Five=5, Dragon=+25, Phoenix=-25 (100 total)
4. Double victory (teammates 1st & 2nd): skip counting, team scores 200 flat
5. Small Tichu bonus: +100 if caller went out 1st, -100 otherwise (independent of hand scoring)
6. Grand Tichu bonus: +200/-200, same logic

---

## State Broadcasting Strategy

The server maintains the full `GameState` but sends **filtered views** to each player:

```python
def create_player_view(game: GameState, player_seat: int) -> dict:
    """Build the state payload for a specific player."""
    player = game.players[player_seat]
    return {
        "phase": game.phase,
        "your_hand": [card.model_dump() for card in player.hand],
        "your_seat": player_seat,
        "players": [
            {
                "name": p.name,
                "seat": p.seat,
                "team": p.team,
                "card_count": len(p.hand),
                "has_gone_out": p.has_gone_out,
                "called_tichu": p.called_tichu,
            }
            for p in game.players
        ],
        "current_player_seat": game.current_player_seat,
        "trick": [
            {"seat": seat, "combination": combo.model_dump()}
            for seat, combo in game.trick
        ],
        "active_wish": game.active_wish,
        "scores": game.scores,
        "round_number": game.round_number,
        "consecutive_passes": game.consecutive_passes,
        "out_order": game.out_order,
        "can_play": is_player_turn(game, player_seat),
        "valid_actions": get_valid_actions(game, player_seat),
    }
```

---

## Phased Build Plan

### Phase 1: Foundation (Estimated: 2-3 sessions with Claude Code)

**Goal:** Backend card models + combination engine with tests.

**Tasks:**
1. Set up project scaffolding (monorepo with `backend/` and `frontend/`)
2. Implement `Card`, `Suit`, `SpecialType` models
3. Implement `deck.py` — create full 56-card Tichu deck, shuffle, deal
4. Implement `combinations.py`:
   - Detection: given cards, identify the combination type
   - Validation: can this combination beat the current trick?
   - Phoenix handling: try all valid substitutions
   - Bomb detection
5. Write thorough unit tests for combinations — this is the trickiest code

**Claude Code prompt to start Phase 1:**
```
Read tichu-architecture.md for context. Set up the backend Python project
with FastAPI. Start with the card models in game/models.py and
game/constants.py, then implement the combination detection and validation
in game/combinations.py. Write comprehensive tests. The combination logic
is the hardest part — handle Phoenix substitution, bomb detection, pair
sequences, and full house comparison correctly per the Tichu rules.
```

### Phase 2: Game Engine (Estimated: 3-4 sessions)

**Goal:** Full game state machine that can play a complete hand.

**Tasks:**
1. Implement `engine.py` — the state machine with all transitions
2. Implement `wish.py` — Mah Jong wish tracking and enforcement
3. Implement `scoring.py` — hand scoring, tichu bonuses, 1000-point check
4. Implement dealing flow: 8 cards → grand tichu → 6 more → push → play
5. Implement turn management: normal turns, skipping out players, hound transfer
6. Implement Dragon trick give-away
7. Implement round-end logic: tailender cards/tricks redistribution
8. Write integration tests: simulate full hands programmatically

**Claude Code prompt to start Phase 2:**
```
Read tichu-architecture.md. Build the game engine in game/engine.py. It
should be a class that manages GameState transitions through all phases:
DEALING → GRAND_TICHU → PUSHING → PLAYING → ROUND_OVER. Implement the
wish system, scoring, and turn management. Write integration tests that
simulate complete hands including edge cases like double victories, Dragon
trick giveaway, and bomb interrupts.
```

### Phase 3: WebSocket Layer (Estimated: 2-3 sessions)

**Goal:** Real-time multiplayer communication.

**Tasks:**
1. Implement `ws/protocol.py` — message type definitions and serialization
2. Implement `ws/handler.py` — connection lifecycle, auth by player name
3. Implement `ws/broadcaster.py` — per-player state view filtering
4. Implement `lobby/manager.py` — create game, join game, room tracking
5. Wire everything together in `main.py`
6. Handle disconnection/reconnection gracefully
7. Test with multiple WebSocket clients (use `websockets` library or Postman)

**Claude Code prompt to start Phase 3:**
```
Read tichu-architecture.md. Build the WebSocket layer. Implement the
lobby manager for creating/joining games, the WebSocket handler for
connection lifecycle, the message protocol, and the broadcaster that
sends filtered game state to each player (hiding opponents' hands).
Wire it all into main.py with FastAPI WebSocket endpoints. Make sure
disconnection is handled — hold the player's seat for 60 seconds so
they can reconnect.
```

### Phase 4: Frontend — Lobby & Game Board (Estimated: 3-4 sessions)

**Goal:** Playable UI.

**Tasks:**
1. Set up Vite + React + TypeScript + Tailwind + Zustand
2. Build lobby: create game → get room code, join game → enter code + name
3. Build waiting room: show 4 seats, team assignments, "start" when full
4. Build game board layout: 4 player positions (you at bottom, partner top, opponents left/right)
5. Build card rendering: fan of cards in hand, click to select, play button
6. Build trick area: show cards played in current trick
7. Build action bar: Play, Pass, Tichu, Bomb buttons with enable/disable logic
8. Build card push UI: select 1 card per opponent + partner
9. Build wish UI: modal to pick a rank when playing Mah Jong
10. Build Dragon give UI: choose which opponent gets the trick
11. Build scoreboard: team scores, tichu call indicators

**Claude Code prompt to start Phase 4:**
```
Read tichu-architecture.md. Set up the React frontend with Vite,
TypeScript, Tailwind, and Zustand. Build the lobby flow first (create
game, join with room code, waiting room showing 4 seats). Then build the
game board — player hand at the bottom (cards fan out, click to select),
partner hand at top, opponents on sides. Center trick area. Action bar
with Play/Pass/Tichu buttons. Use the WebSocket hook to connect to the
backend and sync state through the Zustand store.
```

### Phase 5: Polish & Edge Cases (Estimated: 2-3 sessions)

**Goal:** Handle all the weird Tichu rules and make it feel good.

**Tasks:**
1. Grand Tichu flow: show first 8 cards, decision modal, then deal remaining
2. Card animations: dealing, playing, trick collection
3. Bomb interrupts: allow bomb button even when it's not your turn
4. Wish indicator: persistent banner showing active wish + who must fulfill
5. Sound effects: card play, bomb, tichu call
6. Game log: scrollable action history
7. Reconnection: rejoin game after disconnect, restore full state
8. Error handling: invalid plays, connection drops, edge case messaging
9. Mobile responsiveness: cards must be playable on phone screens

---

## Architecture Decisions & Rationale

**Why in-memory state (no database for MVP)?**
For the MVP, games are ephemeral. Storing state in Python dicts on the server is simpler and faster. If you later want persistence, game history, or horizontal scaling, add Redis or PostgreSQL. The `GameState` Pydantic model serializes cleanly to JSON, so migration is straightforward.

**Why server-authoritative?**
All game logic runs on the server. The client sends intentions ("I want to play these cards"), the server validates and broadcasts results. This prevents cheating and keeps game logic in one place. The client does light validation (highlighting playable combinations) for UX only.

**Why Zustand over Redux?**
Zustand is far less boilerplate for a game where state updates come from WebSocket messages. A single `gameStore` with a `handleMessage(msg)` action that pattern-matches on message type is clean and sufficient.

**Why not Socket.IO?**
FastAPI's native WebSocket support is sufficient for 4-player rooms. Socket.IO adds reconnection and rooms abstractions, but for the MVP, manual reconnection logic (hold seat for 60s, client retries with game_id + player_id) is simpler than adding a Socket.IO Python dependency.

---

## Development Environment Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic websockets pytest pytest-asyncio

# Frontend
cd frontend
npm create vite@latest . -- --template react-ts
npm install zustand
npm install -D tailwindcss @tailwindcss/vite

# Run
cd backend && uvicorn main:app --reload --port 8000
cd frontend && npm run dev
```

## Key Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Combination validation bugs | Exhaustive unit tests with edge cases (Phoenix in bombs, Mah Jong in straights) |
| Wish enforcement complexity | Dedicated `wish.py` module with its own test suite |
| WebSocket state desync | Server is single source of truth; broadcast full state after every action |
| Bomb out-of-turn timing | Server accepts bombs from any active player at any time during PLAYING phase; process in message order |
| Mobile card selection UX | Design card fan with touch targets ≥ 44px; test early on phone |
