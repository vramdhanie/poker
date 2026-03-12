"""Texas Hold'em game engine."""

from __future__ import annotations

import random
import time
from typing import Optional

from .cards import Card, Deck, format_hand, format_community
from .display import (
    clear, separator, header, fmt_money, fmt_pot, fmt_name,
    menu, prompt, info, success, warn, error, action_log, press_enter,
    BOLD, DIM, GREEN, YELLOW, CYAN, MAGENTA, RED, WHITE, RESET, BLUE,
)
from .evaluator import best_hand, hand_name
from .player import Action, AIPlayer, Player, AI_PROFILES
from .save_load import save_game, load_game, delete_save, has_save


STARTING_STACK   = 1_000
SMALL_BLIND      = 10
BIG_BLIND        = 20
AI_THINK_DELAY   = 0.6   # seconds


# ─── Game State ───────────────────────────────────────────────────────────────

class GameState:
    def __init__(self, player_name: str, stack: int = STARTING_STACK) -> None:
        self.human = Player(name=player_name, stack=stack, is_human=True)
        self.ai_players: list[AIPlayer] = [
            AIPlayer(AI_PROFILES[i], stack=STARTING_STACK)
            for i in range(3)
        ]
        self.hand_number: int = 0
        self.dealer_index: int = 0   # index into all_players

    @property
    def all_players(self) -> list[Player]:
        return [self.human] + self.ai_players  # type: ignore[list-item]

    def to_dict(self) -> dict:
        return {
            "player_name": self.human.name,
            "human_stack": self.human.stack,
            "human_wins": self.human.wins,
            "human_hands": self.human.hands_played,
            "ai_stacks": [ai.stack for ai in self.ai_players],
            "ai_wins": [ai.wins for ai in self.ai_players],
            "hand_number": self.hand_number,
            "dealer_index": self.dealer_index,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        gs = cls(data["player_name"], data["human_stack"])
        gs.human.wins = data.get("human_wins", 0)
        gs.human.hands_played = data.get("human_hands", 0)
        for i, ai in enumerate(gs.ai_players):
            ai.stack = data["ai_stacks"][i]
            ai.wins = data.get("ai_wins", [0, 0, 0])[i]
        gs.hand_number = data.get("hand_number", 0)
        gs.dealer_index = data.get("dealer_index", 0)
        return gs


# ─── Hand Engine ──────────────────────────────────────────────────────────────

class Hand:
    """Manages one complete hand of Texas Hold'em."""

    def __init__(self, game_state: GameState) -> None:
        self.gs = game_state
        self.deck = Deck()
        self.community: list[Card] = []
        self.pot: int = 0
        self.side_pots: list[tuple[int, list[Player]]] = []
        self.street: str = "preflop"

        # Rotate dealer
        players = self.gs.all_players
        self.gs.dealer_index %= len(players)
        for p in players:
            p.is_dealer = False
        players[self.gs.dealer_index].is_dealer = True

        # Active players for this hand
        self.players: list[Player] = [p for p in players if p.stack > 0]
        # Seat ordering starting left of dealer
        dealer_pos = self.gs.dealer_index % len(self.players)
        self.players = self.players[dealer_pos + 1:] + self.players[:dealer_pos + 1]
        # Dealer is last in this rotation

    def run(self) -> Optional[Player]:
        """Run a complete hand. Returns the winner(s) for display."""
        if len(self.players) < 2:
            return None

        # Reset players
        for p in self.players:
            p.reset_for_hand()
            p.hands_played += 1

        self.deck.shuffle()
        self._deal_hole_cards()

        # Post blinds
        sb_player = self.players[0] if len(self.players) > 2 else self.players[-2]
        bb_player = self.players[1] if len(self.players) > 2 else self.players[-1]

        sb_posted = sb_player.place_bet(min(SMALL_BLIND, sb_player.stack + sb_player.current_bet))
        self.pot += sb_posted
        bb_posted = bb_player.place_bet(min(BIG_BLIND, bb_player.stack + bb_player.current_bet))
        self.pot += bb_posted

        # --- Streets ---
        still_playing = self._betting_round(
            street="preflop",
            current_bet=BIG_BLIND,
            start_idx=2 % len(self.players),
        )
        if not still_playing:
            return self._award_pot_no_showdown()

        # Flop
        self.community += self.deck.deal(3)
        still_playing = self._betting_round(street="flop", current_bet=0, start_idx=0)
        if not still_playing:
            return self._award_pot_no_showdown()

        # Turn
        self.community += self.deck.deal(1)
        still_playing = self._betting_round(street="turn", current_bet=0, start_idx=0)
        if not still_playing:
            return self._award_pot_no_showdown()

        # River
        self.community += self.deck.deal(1)
        still_playing = self._betting_round(street="river", current_bet=0, start_idx=0)
        if not still_playing:
            return self._award_pot_no_showdown()

        return self._showdown()

    def _deal_hole_cards(self) -> None:
        for p in self.players:
            p.hole_cards = self.deck.deal(2)

    # ─── Display ──────────────────────────────────────────────────────────────

    def _render_table(self, street: str, current_bet: int, highlight: Optional[Player] = None) -> None:
        clear()
        human = self.gs.human

        print(f"\n  {BOLD}{CYAN}── Hand #{self.gs.hand_number}  ·  {street.upper()} ──{RESET}")
        print()

        # Community cards
        community_label = {
            "preflop": "Waiting for flop...",
            "flop":    "Flop",
            "turn":    "Turn",
            "river":   "River",
        }.get(street, street)
        print(f"  {YELLOW}{BOLD}Community ({community_label}):{RESET}")
        print(f"  {format_community(self.community)}")
        print()

        # Pot
        print(f"  {BOLD}Pot:{RESET} {fmt_pot(self.pot)}     "
              f"{BOLD}Current bet:{RESET} {fmt_money(current_bet)}")
        print()
        print(f"  {separator()}")

        # Players
        for p in self.players:
            marker = f"{YELLOW}▶ {RESET}" if p is highlight else "  "
            name_str = fmt_name(p.name, p.is_human, p.folded, p.all_in)
            dealer_tag = f" {DIM}[D]{RESET}" if p.is_dealer else ""
            stack_str = fmt_money(p.stack)
            bet_str = f"{DIM}bet: {fmt_money(p.current_bet)}{RESET}" if p.current_bet else ""

            if p.is_human:
                cards_str = format_hand(p.hole_cards)
            elif not p.folded and self.street == "showdown":
                cards_str = format_hand(p.hole_cards)
            else:
                cards_str = format_hand(p.hole_cards, hide=not p.is_human and not p.folded)

            print(f"  {marker}{name_str}{dealer_tag}  {stack_str}  {bet_str}")
            print(f"      {cards_str}")
            print()

        # Human's hand info (if cards dealt)
        if human.hole_cards and not human.folded and street != "preflop":
            rank, _, _ = best_hand(human.hole_cards, self.community)
            print(f"  {CYAN}Your hand: {BOLD}{hand_name(rank)}{RESET}")
            print()

    # ─── Betting Round ────────────────────────────────────────────────────────

    def _betting_round(self, street: str, current_bet: int, start_idx: int) -> bool:
        """
        Run one betting round. Returns False if all but one player folded.
        Uses a 'last aggressor' model: betting ends when action gets back to
        the last player who raised (or everyone has acted once post-check).
        """
        self.street = street
        active = [p for p in self.players if p.can_act()]
        if len(active) <= 1:
            return True

        # Reset per-round bets
        for p in self.players:
            p.reset_for_round()

        # For preflop, restore blinds already posted
        if street == "preflop":
            if len(self.players) > 2:
                self.players[0].current_bet = SMALL_BLIND
                self.players[1].current_bet = BIG_BLIND
            else:
                self.players[-2].current_bet = SMALL_BLIND
                self.players[-1].current_bet = BIG_BLIND

        num_players = len(self.players)
        # Track who needs to act: initially everyone who can act
        needs_to_act: set[int] = {
            i for i, p in enumerate(self.players) if p.can_act()
        }
        # Start from start_idx
        order = list(range(start_idx, start_idx + num_players))

        acted = 0  # how many have acted since last aggression

        for i in order + order:  # two passes max
            real_i = i % num_players
            p = self.players[real_i]

            if not p.can_act():
                continue
            if real_i not in needs_to_act:
                continue

            needs_to_act.discard(real_i)

            # Compute call amount
            call_amount = max(0, current_bet - p.current_bet)
            if call_amount > p.stack:
                call_amount = p.stack

            # Minimum raise (must raise by at least BIG_BLIND or the last raise size)
            min_raise_to = max(current_bet + BIG_BLIND, current_bet * 2)
            min_raise = min_raise_to - p.current_bet
            min_raise = max(1, min(min_raise, p.stack))
            max_raise = p.stack

            # Render table
            self._render_table(street, current_bet, highlight=p)

            # Get action
            if p.is_human:
                action, amount = self._human_action(p, call_amount, min_raise, max_raise, current_bet)
            else:
                action, amount = self._ai_action(p, call_amount, min_raise, max_raise, street)

            # Apply action
            self._apply_action(p, action, amount, call_amount)
            acted += 1

            if action in (Action.RAISE, Action.ALL_IN):
                new_bet = p.current_bet
                if new_bet > current_bet:
                    current_bet = new_bet
                    # Everyone else who can act must respond
                    needs_to_act = {
                        j for j, q in enumerate(self.players)
                        if q.can_act() and j != real_i
                    }

            # Check if only one player left
            remaining = [x for x in self.players if not x.folded]
            if len(remaining) == 1:
                return False

            # If nobody needs to act, we're done
            if not needs_to_act:
                break

            # Safety: everyone all-in
            if not any(q.can_act() for q in self.players):
                break

        return True

    def _human_action(
        self, p: Player, call_amount: int, min_raise: int, max_raise: int, current_bet: int
    ) -> tuple[Action, int]:
        can_check = call_amount == 0
        can_raise = max_raise >= min_raise

        options = []
        if can_check:
            options.append(("C", "Check"))
        else:
            options.append(("C", f"Call  {fmt_money(call_amount)}"))
        if can_raise:
            options.append(("R", f"Raise  (min {fmt_money(min_raise)})"))
        options.append(("A", f"All In  {fmt_money(p.stack)}"))
        options.append(("F", "Fold"))

        menu(options)

        while True:
            choice = prompt("Your action").upper()

            if choice == "C":
                if can_check:
                    action_log(f"You check.")
                    return (Action.CHECK, 0)
                else:
                    action_log(f"You call {fmt_money(call_amount)}.")
                    return (Action.CALL, call_amount)

            elif choice == "R" and can_raise:
                while True:
                    raw = prompt(f"Raise amount (min {min_raise}, max {max_raise})")
                    try:
                        amount = int(raw)
                        if amount < min_raise:
                            warn(f"Minimum raise is ${min_raise}")
                        elif amount > max_raise:
                            warn(f"Maximum raise is ${max_raise}")
                        else:
                            action_log(f"You raise to {fmt_money(p.current_bet + amount)}.")
                            return (Action.RAISE, amount)
                    except ValueError:
                        warn("Please enter a number.")

            elif choice == "A":
                action_log(f"You go ALL IN with {fmt_money(p.stack)}!")
                return (Action.ALL_IN, p.stack)

            elif choice == "F":
                action_log("You fold.")
                return (Action.FOLD, 0)

            else:
                warn("Invalid choice. " + ("Options: C/R/A/F" if can_raise else "Options: C/A/F"))

    def _ai_action(
        self, p: AIPlayer, call_amount: int, min_raise: int, max_raise: int, street: str
    ) -> tuple[Action, int]:
        # Compute position (0=early, 1=mid, 2=late)
        active = [x for x in self.players if not x.folded]
        pos = active.index(p) if p in active else 0
        position = min(2, pos * 2 // max(len(active), 1))

        action, amount = p.decide(
            community_cards=self.community,
            pot=self.pot,
            call_amount=call_amount,
            min_raise=min_raise,
            max_raise=max_raise,
            position=position,
            street=street,
            num_active=len(active),
        )

        # Simulate thinking
        time.sleep(AI_THINK_DELAY)

        return action, amount

    def _apply_action(self, p: Player, action: Action, amount: int, call_amount: int) -> None:
        if action == Action.FOLD:
            p.folded = True
            action_log(f"{p.name} folds.")

        elif action == Action.CHECK:
            action_log(f"{p.name} checks.")

        elif action == Action.CALL:
            actual = p.place_bet(call_amount)
            self.pot += actual
            action_log(f"{p.name} calls {fmt_money(actual)}.")

        elif action == Action.RAISE:
            # amount is the raise increment above current_bet
            actual = p.place_bet(amount)
            self.pot += actual
            action_log(f"{p.name} raises to {fmt_money(p.current_bet)}.")

        elif action == Action.ALL_IN:
            actual = p.place_bet(p.stack)  # place all remaining stack
            self.pot += actual
            action_log(f"{p.name} goes ALL IN ({fmt_money(p.current_bet)})!")

        press_enter() if p.is_human else time.sleep(0.2)

    # ─── Pot Award ────────────────────────────────────────────────────────────

    def _award_pot_no_showdown(self) -> Player:
        winners = [p for p in self.players if not p.folded]
        winner = winners[0]
        winner.stack += self.pot
        winner.wins += 1
        self.gs.hand_number += 1
        self.gs.dealer_index += 1

        clear()
        print(f"\n  {separator()}")
        success(f"{winner.name} wins {fmt_pot(self.pot)} (all others folded)!")
        print(f"  {separator()}")
        press_enter()
        return winner

    def _showdown(self) -> Player:
        """Evaluate hands and award pot."""
        active = [p for p in self.players if not p.folded]
        self.street = "showdown"

        results = []
        for p in active:
            rank, tiebreak, best5 = best_hand(p.hole_cards, self.community)
            results.append((rank, tiebreak, p, best5))

        results.sort(key=lambda x: (x[0], x[1]), reverse=True)

        # Find all winners (could be a split)
        top_rank, top_tie = results[0][0], results[0][1]
        winners = [r for r in results if r[0] == top_rank and r[1] == top_tie]

        split = self.pot // len(winners)
        remainder = self.pot % len(winners)

        self._render_table("showdown", 0)
        print(f"\n  {BOLD}{YELLOW}═══ SHOWDOWN ═══{RESET}\n")

        for rank, tiebreak, p, best5 in results:
            cards_str = "  ".join(f"[{c}]" for c in best5)
            hn = hand_name(rank)
            is_winner = any(w[2] is p for w in winners)
            tag = f" {GREEN}{BOLD}◀ WINNER{RESET}" if is_winner else ""
            print(f"  {fmt_name(p.name, p.is_human)}:  {hn}  →  {cards_str}{tag}")

        print()

        for _, _, winner, _ in winners:
            award = split + (remainder if winner is winners[0][2] else 0)
            winner.stack += award
            winner.wins += 1
            success(f"{winner.name} wins {fmt_pot(award)}!")

        self.gs.hand_number += 1
        self.gs.dealer_index += 1
        press_enter()
        return winners[0][2]


# ─── Session (multi-hand loop) ────────────────────────────────────────────────

class PokerSession:
    """Manages the overall game session and menus."""

    def __init__(self) -> None:
        self.gs: Optional[GameState] = None

    # ─── Main Menu ────────────────────────────────────────────────────────────

    def main_menu(self) -> None:
        while True:
            clear()
            from .display import print_title
            print_title()

            options = [("N", "New Game")]
            if has_save():
                options.append(("R", "Resume Game"))
            options.append(("Q", "Quit"))

            menu(options)
            choice = prompt("Select").upper()

            if choice == "N":
                self._new_game()
            elif choice == "R" and has_save():
                self._resume_game()
            elif choice == "Q":
                info("Thanks for playing! Goodbye.")
                break
            else:
                warn("Invalid choice.")
                time.sleep(0.8)

    # ─── New Game ─────────────────────────────────────────────────────────────

    def _new_game(self) -> None:
        clear()
        from .display import print_title
        print_title()

        if has_save():
            warn("This will overwrite your saved game.")
            confirm = prompt("Are you sure? (y/N)").lower()
            if confirm != "y":
                return
            delete_save()

        name = prompt("Enter your name")
        if not name:
            name = "Player"

        self.gs = GameState(player_name=name)
        self._play_session()

    # ─── Resume Game ──────────────────────────────────────────────────────────

    def _resume_game(self) -> None:
        data = load_game()
        if not data:
            error("Could not load save file.")
            press_enter()
            return

        self.gs = GameState.from_dict(data)
        info(f"Welcome back, {self.gs.human.name}!")
        info(f"Stack: {fmt_money(self.gs.human.stack)}  |  Hand #{self.gs.hand_number}")
        press_enter()
        self._play_session()

    # ─── Play Session ─────────────────────────────────────────────────────────

    def _play_session(self) -> None:
        assert self.gs is not None

        while True:
            # Check if human is broke
            if self.gs.human.stack <= 0:
                self._game_over()
                return

            # Rebuy broke AI players
            for ai in self.gs.ai_players:
                if ai.stack <= 0:
                    ai.stack = STARTING_STACK
                    action_log(f"{ai.name} rebuys for {fmt_money(STARTING_STACK)}.")

            # Between-hand menu
            action = self._between_hand_menu()
            if action == "save_quit":
                save_game(self.gs.to_dict())
                success(f"Game saved to {CYAN}~/.poker_save.json{RESET}")
                press_enter()
                return
            elif action == "quit":
                return

            # Play a hand
            self.gs.hand_number += 0  # already incremented inside Hand
            hand = Hand(self.gs)
            hand.run()

            # Save after every hand
            save_game(self.gs.to_dict())

    def _between_hand_menu(self) -> str:
        clear()
        assert self.gs is not None
        gs = self.gs

        print(f"\n  {BOLD}{CYAN}── Player Status ──{RESET}\n")
        for p in gs.all_players:
            dealer = f" {DIM}[D]{RESET}" if p.is_dealer else ""
            wins = f"  wins: {p.wins}"
            print(f"  {fmt_name(p.name, p.is_human)}  {fmt_money(p.stack)}{dealer}{DIM}{wins}{RESET}")

        print(f"\n  {BOLD}Hand #{gs.hand_number + 1}{RESET}   "
              f"Blinds: {fmt_money(SMALL_BLIND)}/{fmt_money(BIG_BLIND)}")

        options = [
            ("D", "Deal next hand"),
            ("S", "Save & Quit"),
            ("Q", "Quit without saving"),
        ]
        menu(options)

        while True:
            choice = prompt("Select").upper()
            if choice == "D":
                return "deal"
            elif choice == "S":
                return "save_quit"
            elif choice == "Q":
                warn("Progress since last save will be lost.")
                confirm = prompt("Are you sure? (y/N)").lower()
                if confirm == "y":
                    return "quit"
            else:
                warn("Invalid choice.")

    def _game_over(self) -> None:
        assert self.gs is not None
        clear()
        print(f"\n  {RED}{BOLD}══════════════════════════════{RESET}")
        print(f"  {RED}{BOLD}   GAME OVER — You're broke!{RESET}")
        print(f"  {RED}{BOLD}══════════════════════════════{RESET}\n")
        info(f"You played {self.gs.human.hands_played} hands.")
        info(f"You won {self.gs.human.wins} hand(s).")
        print()
        delete_save()

        choice = prompt("Start a new game? (y/N)").lower()
        if choice == "y":
            name = self.gs.human.name
            self.gs = GameState(player_name=name)
            self._play_session()
