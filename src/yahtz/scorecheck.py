"""src/yaht/validate.py"""

from enum import Enum, auto
from functools import cache
from typing import TYPE_CHECKING

from yahtz.boxes import Box, Section
from yahtz.dicetypes import DiceRoll
from yahtz.exceptions import InvalidBoxError

if TYPE_CHECKING:
    from yahtz.scorecard import ScorecardLike  # Needed to avoid circular dependency


class Scoreability(Enum):
    """Encapsulates the three flavors of Scoreability.

    NOT_SCOREABLE: Either the scoring box has already been scored, or the
    roll does not met the combination requirements of the joker rules prevent
    scoring the selected box.

    POINTS_SCOREABLE: Can be scored for points.  Box is unscored, joker
    requirements (if any) have been met, and box combination requirements
    have been meet (e.g., [2, 2, 2, 2, 5] -> 4 of a kind).

    ZERO_SCOREABLE: Can be scored, but only as zero.  Box is unscored,
    joker requirements (if any) have been met, but box combination
    requirements have not been met (e.g, [2, 2, 2, 5, 5] -> 4 of a kind).

    """

    NOT_SCOREABLE = auto()
    POINTS_SCOREABLE = auto()
    ZERO_SCOREABLE = auto()


@cache
def calculate_score(box: Box, roll: DiceRoll) -> int:
    """For POINTS_SCOREABLE rolls, calculate the points scored."""
    match box:
        case Box(section=Section.UPPER):
            return _calculate_upper_score(box, roll)
        case Box.FULL_HOUSE:
            return 25
        case Box.SMALL_STRAIGHT:
            return 30
        case Box.LARGE_STRAIGHT:
            return 40
        case Box.YAHTZEE:
            return 50
        case Box.THREE_OF_A_KIND | Box.FOUR_OF_A_KIND | Box.CHANCE:
            return sum(roll)
        case _:
            raise InvalidBoxError(f"Unknown box: {box}")


def _calculate_upper_score(box: Box, roll: DiceRoll) -> int:
    """Sum only dice values matching box (e.g, Twos: [2, 3, 4, 2, 5] -> 4."""
    target_number = box.die_number
    return sum(n for n in roll if n == target_number)


@cache
def check_scoreability(
    box: Box,
    roll: DiceRoll,
    card: "ScorecardLike",
) -> Scoreability:
    """True if combo is playable for the specified box/card else False."""

    # Cannot score a box that is already scored
    if _is_scored(box, card):
        return Scoreability.NOT_SCOREABLE

    if _joker_rules_active(roll, card):
        return _check_joker_scoreability(box, roll, card)

    return _check_standard_scoreability(box, roll)


def _is_scored(box: Box, card: "ScorecardLike") -> bool:
    """Checks to see if card box is already scored."""
    return card.box_scores[box] is not None


def _joker_rules_active(roll: DiceRoll, card: "ScorecardLike") -> bool:
    return Box.YAHTZEE in roll and _is_scored(Box.YAHTZEE, card)


def _check_joker_scoreability(
    box: Box, roll: DiceRoll, card: "ScorecardLike"
) -> Scoreability:
    # Under joker rules, free upper matching box must be scored first
    matched_box = Box.from_scoring_number(roll[0])
    if not _is_scored(matched_box, card):
        return (
            Scoreability.POINTS_SCOREABLE
            if box == matched_box
            else Scoreability.NOT_SCOREABLE
        )

    lower_boxes = set(Box.get_lower_boxes())
    # If upper matching box is scored then any lower box is playable
    if box in lower_boxes:
        return Scoreability.POINTS_SCOREABLE

    # Can only play a non-matching upper box if all lower boxes scored
    no_free_lower_boxes = all(_is_scored(c, card) for c in lower_boxes)
    return (
        Scoreability.POINTS_SCOREABLE
        if no_free_lower_boxes
        else Scoreability.NOT_SCOREABLE
    )


def _check_standard_scoreability(box: Box, roll: DiceRoll) -> Scoreability:
    return Scoreability.POINTS_SCOREABLE if box in roll else Scoreability.ZERO_SCOREABLE
