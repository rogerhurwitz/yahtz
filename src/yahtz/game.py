from dataclasses import dataclass
from typing import TYPE_CHECKING

from yahtz.dicetypes import DiceCup
from yahtz.exceptions import InvalidBoxError
from yahtz.scorecard import Scorecard, ScorecardView
from yahtz.scorecheck import Scoreability, check_scoreability

if TYPE_CHECKING:
    from yahtz.player import Player


@dataclass
class PlayerGameState:
    dice_cup: DiceCup
    card: ScorecardView


class Game:
    def __init__(self, players: list["Player"]):
        """Initialize game state."""
        if not players:
            raise ValueError("At least one player is required")

        self._players = players

        # Resettable attributes
        self._current_player_index: int
        self._has_final_results: bool
        self._scorecards: dict["Player", Scorecard]
        self._dice_cups: dict["Player", DiceCup]

        self._reset()

    def _reset(self) -> None:
        self._current_player_index = 0
        self._has_final_results = False
        self._scorecards: dict["Player", Scorecard] = {}
        self._dice_cups: dict["Player", DiceCup] = {}
        for player in self._players:
            self._scorecards[player] = Scorecard()
            self._dice_cups[player] = DiceCup()

    def play_game(self) -> None:
        """Run the full game loop until completion."""
        self._reset()
        while not self._is_game_over():
            current_player = self._current_player()
            self._play_turn(current_player)
            self._next_player()
        self._has_final_results = True

    @property
    def winning_players(self) -> list["Player"] | None:
        """Returns winning player(s) at the end of the game."""
        if not self._has_final_results:
            return None

        # Find the highest score
        max_score = max(
            self._scorecards[player].get_card_score() for player in self._players
        )

        # Return all players with the highest score
        winners = [
            player
            for player in self._players
            if self._scorecards[player].get_card_score() == max_score
        ]

        return winners

    def get_final_scores(self) -> list[tuple[str, int]]:
        """Returns a list of (player_name, score) tuples sorted by score (highest first)."""
        if not self._has_final_results:
            raise ValueError("Game is not over yet")

        scores = [
            (player.name, self._scorecards[player].get_card_score())
            for player in self._players
        ]
        return sorted(scores, key=lambda x: x[1], reverse=True)

    def get_game_summary(self) -> str:
        """Returns a formatted string summary of the game results."""
        if not self._has_final_results:
            raise ValueError("Game is not over yet")

        scores = self.get_final_scores()
        winners = self.winning_players

        summary = "=== YAHTZEE GAME RESULTS ===\n"
        for i, (name, score) in enumerate(scores, 1):
            summary += f"{i}. {name}: {score} points\n"

        if winners is not None:
            if len(winners) == 1:
                summary += f"\n🏆 Winner: {winners[0].name}!"
            else:
                winner_names = [player.name for player in winners]
                summary += f"\n🏆 Tie between: {', '.join(winner_names)}!"

        return summary

    def get_detailed_results(self) -> dict[str, dict[str, int]]:
        """Returns detailed scoring data for all players in JSON-serializable format.

        Returns a dictionary where:
        - Keys are player names
        - Values are dictionaries containing all scoring boxes, bonuses, and totals
        """
        if not self._has_final_results:
            raise ValueError("Game is not over yet")

        results: dict[str, dict[str, int]] = {}

        for player in self._players:
            scorecard = self._scorecards[player]
            player_data = {}

            # Add all box scores
            for box in scorecard.box_scores:
                score = scorecard.box_scores[box]
                player_data[box.name] = score if score is not None else 0

            # Calculate and add upper section total
            upper_total = sum(
                scorecard.box_scores[box] or 0
                for box in scorecard.box_scores
                if box.section.name == "UPPER"
            )
            player_data["UPPER_SECTION_TOTAL"] = upper_total

            # Add upper section bonus
            upper_bonus = 35 if upper_total >= 63 else 0
            player_data["UPPER_SECTION_BONUS"] = upper_bonus

            # Calculate and add lower section total
            lower_total = sum(
                scorecard.box_scores[box] or 0
                for box in scorecard.box_scores
                if box.section.name == "LOWER"
            )
            player_data["LOWER_SECTION_TOTAL"] = lower_total

            # Add Yahtzee bonus count and points
            player_data["YAHTZEE_BONUS_COUNT"] = scorecard.yahtzee_bonus_count
            player_data["YAHTZEE_BONUS_POINTS"] = scorecard.yahtzee_bonus_count * 100

            # Add grand total
            player_data["GRAND_TOTAL"] = scorecard.get_card_score()

            results[player.name] = player_data

        return results

    def _play_turn(self, player: "Player") -> None:
        """Internal method to run a full turn for the given player."""
        # Reset the dice cup for this turn
        dice_cup = DiceCup()
        self._dice_cups[player] = dice_cup

        # Create the game state for the player
        scorecard = self._scorecards[player]
        game_state = PlayerGameState(dice_cup=dice_cup, card=scorecard.view)

        # Let the player take their turn and choose a box
        chosen_box = player.take_turn(game_state)

        # Get the final dice roll from the cup
        final_roll = dice_cup.current_role
        if final_roll is None:
            raise ValueError("Player must roll dice at least once during their turn")

        # Score the chosen box - let exceptions propagate
        match check_scoreability(chosen_box, final_roll, scorecard):
            case Scoreability.NOT_SCOREABLE:
                raise InvalidBoxError(f"Unscoreable box: {chosen_box.name}")
            case Scoreability.POINTS_SCOREABLE:
                scorecard.set_box_score(chosen_box, final_roll)
            case Scoreability.ZERO_SCOREABLE:
                scorecard.zero_box(chosen_box, final_roll)

    def _is_game_over(self) -> bool:
        """Internal: returns True if all players have completed all 13 turns."""
        # Game is over when all players have filled all 13 boxes
        for player in self._players:
            scorecard = self._scorecards[player]
            if len(scorecard.get_unscored_boxes()) > 0:
                return False
        return True

    def _next_player(self) -> "Player":
        """Internal method returns the next player in the turn."""
        self._current_player_index = (self._current_player_index + 1) % len(self._players)
        return self._current_player()

    def _current_player(self) -> "Player":
        """Internal method returns the current player in the turn."""
        return self._players[self._current_player_index]
