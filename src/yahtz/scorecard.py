# src/yaht/scorecard.py

from typing import Any, Callable, Protocol

from yahtz.boxes import Box
from yahtz.dicetypes import DiceRoll
from yahtz.exceptions import (
    BoxAlreadyScored,
    InvalidBoxError,
)
from yahtz.scorecheck import Scoreability, calculate_score, check_scoreability

UPPER_BONUS_SCORE = 35
UPPER_BONUS_THRESHOLD = 63
YAHTZEE_BONUS_SCORE = 100


class ScorecardLike(Protocol):
    box_scores: dict[Box, int | None]


class ScorecardView:
    def __init__(
        self,
        get_card_score: Callable[[], int],
        box_scores: dict[Box, int | None],
    ):
        self._card_get_score = get_card_score
        self.box_scores = box_scores

    def __eq__(self, other: Any) -> bool:
        """Check equality with another DiceRoll (order independent)."""
        if not isinstance(other, (ScorecardView, Scorecard)):
            return False
        return self.box_scores == other.box_scores

    def __hash__(self) -> int:
        """Make DiceRoll hashable (useful for sets/dicts)."""
        return hash(tuple(self.box_scores.values()))

    def get_unscored_boxes(self) -> list[Box]:
        return [c for c in self.box_scores if self.box_scores[c] is None]

    def get_card_score(self) -> int:
        return self._card_get_score()


class Scorecard:
    """Tracks the score for a single player."""

    def __init__(self):
        # Initialize all boxes to None (not scored yet)
        self.box_scores: dict[Box, int | None] = {box: None for box in Box}
        self.yahtzee_bonus_count = 0

    def __eq__(self, other: Any) -> bool:
        """Check equality with another DiceRoll (order independent)."""
        if not isinstance(other, (ScorecardView, Scorecard)):
            return False
        return self.box_scores == other.box_scores

    def __hash__(self) -> int:
        """Make DiceRoll hashable (useful for sets/dicts)."""
        return hash(tuple(self.box_scores.values()))

    def zero_box(self, box: Box, roll: DiceRoll) -> None:
        if self.box_scores[box] is not None:
            raise BoxAlreadyScored(f"Box {box.name} has already been scored")
        self.box_scores[box] = 0

        # Award Yahtzee bonus if applicable
        if Box.YAHTZEE in roll and self.box_scores.get(Box.YAHTZEE) == 50:
            self.yahtzee_bonus_count += 1

    def set_box_score(self, box: Box, roll: DiceRoll) -> None:
        """Set score for specified box based on dice values."""

        #  --- Check for Input Errors  ---

        if box not in self.box_scores:
            raise InvalidBoxError(f"Unknown box: {box}")

        if self.box_scores[box] is not None:
            raise BoxAlreadyScored(f"Box {box.name} has already been scored")

        # --- Validate playability ---
        if check_scoreability(box, roll, self) == Scoreability.NOT_SCOREABLE:
            raise InvalidBoxError(f"Unplayable {box.name} combination: {roll}")

        # --- Begin Scoring Dice ---

        # Handle Yahtzee bonus first
        if Box.YAHTZEE in roll and self.box_scores[Box.YAHTZEE] == 50:
            self.yahtzee_bonus_count += 1

        # Call the appropriate scorer
        self.box_scores[box] = calculate_score(box, roll)

    def get_card_score(self) -> int:
        """Get the score across all boxes including bonuses."""
        upper_score = sum(self.box_scores[box] or 0 for box in Box.get_upper_boxes())

        lower_score = sum(self.box_scores[box] or 0 for box in Box.get_lower_boxes())

        upper_bonus = UPPER_BONUS_SCORE if upper_score >= UPPER_BONUS_THRESHOLD else 0
        yahtzee_bonus = self.yahtzee_bonus_count * YAHTZEE_BONUS_SCORE

        return upper_score + upper_bonus + lower_score + yahtzee_bonus

    def get_unscored_boxes(self) -> list[Box]:
        """Return a list of boxes that have not been scored yet."""
        return [box for box, score in self.box_scores.items() if score is None]

    def __str__(self) -> str:
        scored = {
            box.name: score for box, score in self.box_scores.items() if score is not None
        }
        return f"Scorecard({scored}, bonuses={self.yahtzee_bonus_count})"

    @property
    def view(self) -> ScorecardView:
        """Return a read-only view of the scorecard."""
        return ScorecardView(self.get_card_score, dict(self.box_scores))
