import unittest

from yahtz.boxes import Box
from yahtz.dicetypes import DiceRoll
from yahtz.scorecard import Scorecard
from yahtz.scorecheck import Scoreability, check_scoreability


class TestIsPlayable(unittest.TestCase):
    def setUp(self):
        self.card = Scorecard()

    # --- Upper Section Tests ---
    def test_upper_box_playable_with_matches(self):
        self.assertEqual(
            check_scoreability(Box.FOURS, DiceRoll([4, 4, 2, 3, 6]), self.card),
            Scoreability.POINTS_SCOREABLE,
        )

    def test_upper_box_playable_with_no_matches(self):
        self.assertEqual(
            check_scoreability(Box.SIXES, DiceRoll([1, 2, 3, 4, 5]), self.card),
            Scoreability.POINTS_SCOREABLE,
        )

    def test_upper_box_unplayable_if_already_scored(self):
        self.card.set_box_score(Box.THREES, DiceRoll([3, 3, 3, 2, 1]))
        self.assertEqual(
            check_scoreability(Box.THREES, DiceRoll([3, 3, 3, 2, 1]), self.card),
            Scoreability.NOT_SCOREABLE,
        )

    # --- Lower Section: Three/Four of a Kind ---
    def test_three_of_a_kind_valid(self):
        self.assertEqual(
            check_scoreability(Box.THREE_OF_A_KIND, DiceRoll([2, 2, 2, 4, 5]), self.card),
            Scoreability.POINTS_SCOREABLE,
        )

    def test_four_of_a_kind_valid(self):
        self.assertEqual(
            check_scoreability(Box.FOUR_OF_A_KIND, DiceRoll([5, 5, 5, 5, 5]), self.card),
            Scoreability.POINTS_SCOREABLE,
        )

    def test_three_of_a_kind_invalid(self):
        self.assertEqual(
            check_scoreability(Box.THREE_OF_A_KIND, DiceRoll([2, 2, 3, 4, 5]), self.card),
            Scoreability.ZERO_SCOREABLE,
        )

    def test_four_of_a_kind_invalid(self):
        self.assertEqual(
            check_scoreability(Box.FOUR_OF_A_KIND, DiceRoll([5, 5, 5, 2, 2]), self.card),
            Scoreability.ZERO_SCOREABLE,
        )

    # --- Lower Section: Full House ---
    def test_full_house_valid(self):
        self.assertEqual(
            check_scoreability(Box.FULL_HOUSE, DiceRoll([3, 3, 3, 6, 6]), self.card),
            Scoreability.POINTS_SCOREABLE,
        )

    def test_full_house_invalid(self):
        self.assertEqual(
            check_scoreability(Box.FULL_HOUSE, DiceRoll([3, 3, 4, 4, 6]), self.card),
            Scoreability.ZERO_SCOREABLE,
        )

    def test_full_house_yahtzee_valid_1(self):
        self.card.zero_box(Box.YAHTZEE, DiceRoll([1, 1, 1, 1, 1]))
        self.card.zero_box(Box.THREES, DiceRoll([3, 4, 5, 2, 1]))
        self.assertEqual(
            check_scoreability(Box.FULL_HOUSE, DiceRoll([3, 3, 3, 3, 3]), self.card),
            Scoreability.POINTS_SCOREABLE,
        )

    def test_full_house_yahtzee_valid_2(self):
        self.assertEqual(
            check_scoreability(Box.FULL_HOUSE, DiceRoll([3, 3, 3, 3, 3]), self.card),
            Scoreability.POINTS_SCOREABLE,
        )

    def test_full_house_yahtzee_invalid(self):
        self.card.zero_box(Box.YAHTZEE, DiceRoll([1, 1, 1, 1, 1]))
        self.assertEqual(
            check_scoreability(Box.FULL_HOUSE, DiceRoll([3, 3, 3, 3, 3]), self.card),
            Scoreability.NOT_SCOREABLE,
        )

    # --- Lower Section: Straights ---
    def test_small_straight_valid(self):
        self.assertEqual(
            check_scoreability(Box.SMALL_STRAIGHT, DiceRoll([1, 2, 3, 4, 6]), self.card),
            Scoreability.POINTS_SCOREABLE,
        )

    def test_small_straight_invalid(self):
        self.assertEqual(
            check_scoreability(Box.SMALL_STRAIGHT, DiceRoll([1, 1, 3, 4, 6]), self.card),
            Scoreability.ZERO_SCOREABLE,
        )

    def test_large_straight_valid(self):
        self.assertEqual(
            check_scoreability(Box.LARGE_STRAIGHT, DiceRoll([2, 3, 4, 5, 6]), self.card),
            Scoreability.POINTS_SCOREABLE,
        )

    def test_large_straight_invalid(self):
        self.assertEqual(
            check_scoreability(Box.LARGE_STRAIGHT, DiceRoll([1, 2, 2, 4, 5]), self.card),
            Scoreability.ZERO_SCOREABLE,
        )

    # --- YAHTZEE ---
    def test_yahtzee_valid(self):
        self.assertEqual(
            check_scoreability(Box.YAHTZEE, DiceRoll([6, 6, 6, 6, 6]), self.card),
            Scoreability.POINTS_SCOREABLE,
        )

    def test_yahtzee_invalid(self):
        self.assertEqual(
            check_scoreability(Box.YAHTZEE, DiceRoll([6, 6, 6, 6, 5]), self.card),
            Scoreability.ZERO_SCOREABLE,
        )

    # --- CHANCE ---
    def test_chance_unscored_always_playable(self):
        self.assertEqual(
            check_scoreability(Box.CHANCE, DiceRoll([1, 2, 3, 4, 5]), self.card),
            Scoreability.POINTS_SCOREABLE,
        )

    def test_chance_scored_unplayable(self):
        self.card.set_box_score(Box.CHANCE, DiceRoll([1, 2, 3, 4, 5]))
        self.assertEqual(
            check_scoreability(Box.CHANCE, DiceRoll([1, 2, 3, 4, 5]), self.card),
            Scoreability.NOT_SCOREABLE,
        )

    # --- Joker Rule Cases ---
    def test_joker_requires_upper_box(self):
        self.card.set_box_score(Box.YAHTZEE, DiceRoll([3, 3, 3, 3, 3]))
        combo = DiceRoll([3, 3, 3, 3, 3])
        self.assertEqual(
            check_scoreability(Box.THREES, combo, self.card),
            Scoreability.POINTS_SCOREABLE,
        )
        self.assertEqual(
            check_scoreability(Box.FULL_HOUSE, combo, self.card),
            Scoreability.NOT_SCOREABLE,
        )

    def test_joker_allows_lower_when_upper_scored(self):
        self.card.set_box_score(Box.YAHTZEE, DiceRoll([4, 4, 4, 4, 4]))
        self.card.set_box_score(Box.FOURS, DiceRoll([4, 4, 4, 4, 4]))
        combo = DiceRoll([4, 4, 4, 4, 4])
        self.assertEqual(
            check_scoreability(Box.FULL_HOUSE, combo, self.card),
            Scoreability.POINTS_SCOREABLE,
        )

    def test_joker_denied_if_all_scored(self):
        for box in Box:
            self.card.zero_box(box, DiceRoll([1, 1, 1, 1, 1]))
        combo = DiceRoll([2] * 5)
        self.assertEqual(
            check_scoreability(Box.THREE_OF_A_KIND, combo, self.card),
            Scoreability.NOT_SCOREABLE,
        )


if __name__ == "__main__":
    unittest.main()
