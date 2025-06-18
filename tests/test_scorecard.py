import unittest
from typing import cast

from yahtz.boxes import Box
from yahtz.dicetypes import DiceRoll
from yahtz.exceptions import (
    BoxAlreadyScored,
    DiceCountError,
    DieValueError,
    InvalidBoxError,
)
from yahtz.scorecard import Scorecard
from yahtz.scorecheck import Scoreability, calculate_score, check_scoreability


class BaseScorecardTest(unittest.TestCase):
    def setUp(self):
        self.card = Scorecard()

    def assert_score(self, box: Box, dice: DiceRoll, expected: int):
        self.card.set_box_score(box, dice)
        self.assertEqual(self.card.box_scores[box], expected)


class TestUpperSection(BaseScorecardTest):
    def test_aces_scoring(self):
        self.assert_score(Box.ACES, DiceRoll([1, 1, 2, 3, 4]), 2)

    def test_zero_score_when_no_dice_match(self):
        self.assert_score(Box.TWOS, DiceRoll([1, 1, 3, 4, 5]), 0)

    def test_upper_bonus_awarded(self):
        for box in Box.get_upper_boxes():
            assert box.die_number is not None
            self.card.set_box_score(box, DiceRoll([box.die_number] * 5))
        self.assertGreaterEqual(self.card.get_card_score(), 63 + 35)  # includes bonus


class TestLowerSection(BaseScorecardTest):
    def test_three_of_a_kind_valid(self):
        self.assert_score(Box.THREE_OF_A_KIND, DiceRoll([2, 2, 2, 4, 5]), 15)

    def test_full_house_scoring(self):
        self.assert_score(Box.FULL_HOUSE, DiceRoll([3, 3, 3, 6, 6]), 25)

    def test_small_straight_valid(self):
        self.assert_score(Box.SMALL_STRAIGHT, DiceRoll([1, 2, 3, 4, 6]), 30)

    def test_large_straight_valid(self):
        self.assert_score(Box.LARGE_STRAIGHT, DiceRoll([2, 3, 4, 5, 6]), 40)

    def test_yahtzee(self):
        self.assert_score(Box.YAHTZEE, DiceRoll([5, 5, 5, 5, 5]), 50)


class TestValidation(BaseScorecardTest):
    def test_invalid_dice_count(self):
        with self.assertRaises(DiceCountError):
            self.card.set_box_score(Box.FOURS, DiceRoll([4, 4, 4]))

    def test_invalid_die_value(self):
        with self.assertRaises(DieValueError):
            self.card.set_box_score(Box.FIVES, DiceRoll([5, 5, 5, 5, 7]))

    def test_box_already_scored(self):
        self.card.set_box_score(Box.THREES, DiceRoll([3, 3, 3, 2, 1]))
        with self.assertRaises(BoxAlreadyScored):
            self.card.set_box_score(Box.THREES, DiceRoll([3, 3, 3, 3, 3]))

    def test_invalid_box(self):
        self.assertEqual(self.card.box_scores.get(cast(Box, "INVALID")), None)


class TestBonuses(BaseScorecardTest):
    def test_yahtzee_bonus_applied(self):
        self.card.set_box_score(Box.YAHTZEE, DiceRoll([6, 6, 6, 6, 6]))
        self.card.set_box_score(Box.SIXES, DiceRoll([6, 6, 6, 6, 6]))
        self.card.set_box_score(Box.THREE_OF_A_KIND, DiceRoll([6, 6, 6, 6, 6]))
        self.assertEqual(self.card.yahtzee_bonus_count, 2)

    def test_joker_rule_blocks_wrong_box(self):
        self.card.set_box_score(Box.YAHTZEE, DiceRoll([3, 3, 3, 3, 3]))
        with self.assertRaises(InvalidBoxError):
            self.card.set_box_score(Box.FOUR_OF_A_KIND, DiceRoll([3, 3, 3, 3, 3]))

    def test_zero_box(self):
        self.card.zero_box(Box.CHANCE, DiceRoll([1, 2, 3, 4, 5]))
        self.assertEqual(self.card.box_scores[Box.CHANCE], 0)

        with self.assertRaises(BoxAlreadyScored):
            self.card.zero_box(Box.CHANCE, DiceRoll([1, 2, 3, 4, 5]))


class TestScoringModule(BaseScorecardTest):
    def test_invalid_box(self):
        with self.assertRaises(Exception):
            calculate_score(cast(Box, "INVALID"), DiceRoll([1, 2, 3, 4, 5]))


class TestOriginalMetrics(BaseScorecardTest):
    def test_scorecard_type(self):
        """Confirm that scorecard is an instance of Scorecard."""
        self.assertIsInstance(self.card, Scorecard)

    def test_initial_score(self):
        """Confirm that scorecard initial score total is zero."""
        self.assertEqual(self.card.get_card_score(), 0)

    def test_yahtzee_scoring(self):
        self.card.set_box_score(Box.YAHTZEE, DiceRoll([6, 6, 6, 6, 6]))
        self.assertEqual(self.card.box_scores[Box.YAHTZEE], 50)

    def test_chance_scoring(self):
        self.card.set_box_score(Box.CHANCE, DiceRoll([1, 2, 3, 4, 5]))
        self.assertEqual(self.card.box_scores[Box.CHANCE], 15)

    def test_null_dice_sets_zero(self):
        self.card.zero_box(Box.FIVES, DiceRoll([1, 2, 3, 4, 5]))
        self.assertEqual(self.card.box_scores[Box.FIVES], 0)

    def test_upper_section_bonus_awarded(self):
        # Score exactly 63: three of each 1–6
        self.card.set_box_score(Box.ACES, DiceRoll([1, 1, 1, 2, 3]))
        self.card.set_box_score(Box.TWOS, DiceRoll([2, 2, 2, 1, 3]))
        self.card.set_box_score(Box.THREES, DiceRoll([3, 3, 3, 2, 1]))
        self.card.set_box_score(Box.FOURS, DiceRoll([4, 4, 4, 1, 2]))
        self.card.set_box_score(Box.FIVES, DiceRoll([5, 5, 5, 1, 2]))
        self.card.set_box_score(Box.SIXES, DiceRoll([6, 6, 6, 1, 2]))
        total = self.card.get_card_score()
        self.assertGreaterEqual(total, 63 + 35)

    def test_joker_rule_used_when_yahtzee_zeroed(self):
        # First YAHTZEE is zeroed
        self.card.zero_box(Box.YAHTZEE, DiceRoll([1, 2, 3, 4, 5]))
        # Later roll a Yahtzee again (e.g., five 4s)
        self.card.set_box_score(Box.FOURS, DiceRoll([4, 4, 4, 4, 4]))
        self.assertEqual(self.card.box_scores[Box.FOURS], 20)

    def test_joker_rule_applies_to_lower_section_if_upper_filled(self):
        # Zero YAHTZEE and fill FOURS
        self.card.zero_box(Box.YAHTZEE, DiceRoll([1, 2, 3, 4, 5]))
        self.card.set_box_score(Box.FOURS, DiceRoll([4, 4, 2, 1, 1]))  # FOURS = 8
        # Now roll five 4s again
        self.card.set_box_score(Box.FULL_HOUSE, DiceRoll([4, 4, 4, 4, 4]))
        self.assertEqual(self.card.box_scores[Box.FULL_HOUSE], 25)

    def test_joker_rule_fallback_zero(self):
        # Zero YAHTZEE and fill all legal options
        self.card.zero_box(Box.YAHTZEE, DiceRoll([1, 2, 3, 4, 5]))
        self.card.set_box_score(Box.FOURS, DiceRoll([4, 4, 2, 1, 1]))
        self.card.set_box_score(Box.FULL_HOUSE, DiceRoll([2, 2, 3, 3, 3]))
        self.card.set_box_score(Box.THREE_OF_A_KIND, DiceRoll([2, 2, 2, 4, 5]))
        self.card.set_box_score(Box.FOUR_OF_A_KIND, DiceRoll([6, 6, 6, 6, 3]))
        self.card.set_box_score(Box.SMALL_STRAIGHT, DiceRoll([1, 2, 3, 4, 6]))
        self.card.set_box_score(Box.LARGE_STRAIGHT, DiceRoll([2, 3, 4, 5, 6]))
        self.card.set_box_score(Box.CHANCE, DiceRoll([1, 1, 1, 2, 3]))
        # Now joker forced to fill a zero in an upper section box
        with self.assertRaises(BoxAlreadyScored):
            self.card.set_box_score(Box.FOURS, DiceRoll([4, 4, 4, 4, 4]))

    def test_reject_illegal_joker_box(self):
        # Zero out the YAHTZEE box
        self.card.zero_box(Box.YAHTZEE, DiceRoll([1, 2, 3, 4, 5]))
        # Fill required Upper Section box (e.g., FOURS)
        self.card.set_box_score(Box.FOURS, DiceRoll([4, 4, 1, 2, 3]))
        # Fill all Lower Section joker targets
        self.card.set_box_score(Box.FULL_HOUSE, DiceRoll([3, 3, 3, 2, 2]))
        self.card.set_box_score(Box.THREE_OF_A_KIND, DiceRoll([2, 2, 2, 4, 5]))
        self.card.set_box_score(Box.FOUR_OF_A_KIND, DiceRoll([6, 6, 6, 6, 1]))
        self.card.set_box_score(Box.SMALL_STRAIGHT, DiceRoll([1, 2, 3, 4, 5]))
        self.card.set_box_score(Box.LARGE_STRAIGHT, DiceRoll([2, 3, 4, 5, 6]))
        self.card.set_box_score(Box.CHANCE, DiceRoll([1, 1, 3, 4, 6]))
        # Try to place a Yahtzee of 4s into Full House again (should fail)
        with self.assertRaises(BoxAlreadyScored):
            self.card.set_box_score(Box.FULL_HOUSE, DiceRoll([4, 4, 4, 4, 4]))

    def test_allow_valid_joker_box_when_upper_box_taken(self):
        self.card.zero_box(Box.YAHTZEE, DiceRoll([1, 2, 3, 4, 5]))
        self.card.set_box_score(Box.FIVES, DiceRoll([5, 5, 1, 2, 3]))
        # YAHTZEE of 5s, valid Joker placement in Chance
        self.card.set_box_score(Box.CHANCE, DiceRoll([5, 5, 5, 5, 5]))
        self.assertEqual(self.card.box_scores[Box.CHANCE], 25)

    def test_reject_invalid_joker_box_when_not_allowed(self):
        self.card.zero_box(Box.YAHTZEE, DiceRoll([1, 2, 3, 4, 5]))
        # YAHTZEE of 6s, SIXES box still open → must use SIXES
        with self.assertRaises(InvalidBoxError):
            self.card.set_box_score(Box.CHANCE, DiceRoll([6, 6, 6, 6, 6]))


class TestGetUnscoredBoxes(BaseScorecardTest):
    def setUp(self):
        self.allcats = [box for box in Box]
        super().setUp()

    def test_no_scored(self):
        unscored = self.card.get_unscored_boxes()
        self.assertEqual(set(unscored), set(self.allcats))

    def test_one_scored(self):
        self.card.zero_box(Box.ACES, DiceRoll([1, 2, 3, 4, 5]))
        unscored = self.card.get_unscored_boxes()
        self.assertFalse(Box.ACES in unscored)
        self.assertEqual(len(unscored), len(self.allcats) - 1)

    def test_two_scored(self):
        self.card.zero_box(Box.ACES, DiceRoll([1, 2, 3, 4, 5]))
        self.card.zero_box(Box.YAHTZEE, DiceRoll([1, 2, 3, 4, 5]))
        unscored = self.card.get_unscored_boxes()
        self.assertFalse(Box.ACES in unscored)
        self.assertFalse(Box.YAHTZEE in unscored)
        self.assertEqual(len(unscored), len(self.allcats) - 2)

    def test_all_scored(self):
        for box in Box:
            self.card.zero_box(box, DiceRoll([1, 2, 3, 4, 5]))
        unscored = self.card.get_unscored_boxes()
        self.assertCountEqual(unscored, [])


# Update the relevant tests to reflect that all unscored Upper Section boxes are playable
class TestGetPlayableBoxes(BaseScorecardTest):
    def test_upper_section_and_small_straight(self):
        dice = DiceRoll([1, 2, 3, 4, 6])
        expected = {
            Box.ACES,
            Box.TWOS,
            Box.THREES,
            Box.FOURS,
            Box.FIVES,  # now explicitly valid even though score would be 0
            Box.SIXES,
            Box.SMALL_STRAIGHT,
            Box.CHANCE,
        }
        playable = [
            box
            for box in Box
            if check_scoreability(box, dice, self.card) == Scoreability.POINTS_SCOREABLE
        ]
        self.assertEqual(set(playable), expected)

    def test_three_of_a_kind_and_upper_options(self):
        dice = DiceRoll([5, 5, 5, 2, 3])
        expected = {
            Box.THREE_OF_A_KIND,
            Box.FIVES,
            Box.TWOS,
            Box.THREES,
            Box.ACES,  # valid even if it would score 0
            Box.FOURS,
            Box.SIXES,
            Box.CHANCE,
        }
        playable = [
            box
            for box in Box
            if check_scoreability(box, dice, self.card) == Scoreability.POINTS_SCOREABLE
        ]
        self.assertEqual(set(playable), expected)

    def test_full_house_included(self):
        dice = DiceRoll([3, 3, 3, 6, 6])
        expected = {
            Box.FULL_HOUSE,
            Box.THREE_OF_A_KIND,
            Box.THREES,
            Box.SIXES,
            Box.ACES,
            Box.TWOS,
            Box.FOURS,
            Box.FIVES,
            Box.CHANCE,
        }
        playable = [
            box
            for box in Box
            if check_scoreability(box, dice, self.card) == Scoreability.POINTS_SCOREABLE
        ]
        self.assertEqual(set(playable), expected)

    def test_yahtzee_joker_rule_behavior(self):
        self.card.set_box_score(Box.YAHTZEE, DiceRoll([6, 6, 6, 6, 6]))
        self.assertEqual(self.card.box_scores[Box.YAHTZEE], 50)

        dice = DiceRoll([6, 6, 6, 6, 6])

        # Case 1: SIXES is open — must use SIXES
        expected = {Box.SIXES}
        playable = [
            box
            for box in Box
            if check_scoreability(box, dice, self.card) == Scoreability.POINTS_SCOREABLE
        ]
        self.assertEqual(set(playable), expected)

        # Case 2: SIXES scored — Joker rules allow specific Lower boxes
        self.card.set_box_score(Box.SIXES, DiceRoll([6, 6, 6, 6, 6]))
        expected = {
            Box.THREE_OF_A_KIND,
            Box.FOUR_OF_A_KIND,
            Box.FULL_HOUSE,
            Box.SMALL_STRAIGHT,
            Box.LARGE_STRAIGHT,
            Box.CHANCE,
        }
        playable = [
            box
            for box in Box
            if check_scoreability(box, dice, self.card) == Scoreability.POINTS_SCOREABLE
        ]
        self.assertEqual(set(playable), expected)

    def test_box_already_scored_excluded(self):
        self.card.set_box_score(Box.FIVES, DiceRoll([5, 5, 5, 2, 3]))
        dice = DiceRoll([5, 5, 5, 2, 3])
        playable = [
            box
            for box in Box
            if check_scoreability(box, dice, self.card) == Scoreability.POINTS_SCOREABLE
        ]
        self.assertNotIn(Box.FIVES, playable)

    def test_unplayable_combo_limited_options(self):
        dice = DiceRoll([1, 1, 2, 2, 3])
        expected = {
            Box.ACES,
            Box.TWOS,
            Box.THREES,
            Box.FOURS,
            Box.FIVES,
            Box.SIXES,
            Box.CHANCE,
        }
        playable = [
            box
            for box in Box
            if check_scoreability(box, dice, self.card) == Scoreability.POINTS_SCOREABLE
        ]
        self.assertEqual(set(playable), expected)


class TestPerfectGame(unittest.TestCase):
    class TestPerfectGame(unittest.TestCase):
        def test_perfect_yahtzee_game_scores_1575(self):
            card = Scorecard()

            # Step 1: Score YAHTZEE with DiceRoll([6,6,6,6,6])
            sixes = [6] * 5
            card.set_box_score(Box.YAHTZEE, DiceRoll(sixes))

            # Step 2: Score SIXES immediately (required by Joker rule)
            card.set_box_score(Box.SIXES, DiceRoll(sixes))

            # Step 3: Score remaining upper boxes with matching Yahtzees
            upper_map = {
                1: Box.ACES,
                2: Box.TWOS,
                3: Box.THREES,
                4: Box.FOURS,
                5: Box.FIVES,
            }
            for face in range(1, 6):  # Already did SIXES
                dice = [face] * 5
                card.set_box_score(upper_map[face], DiceRoll(dice))

            # Step 4: Score lower boxes using Joker logic
            lower_boxes = [
                Box.FULL_HOUSE,  # 25
                Box.SMALL_STRAIGHT,  # 30
                Box.LARGE_STRAIGHT,  # 40
                Box.THREE_OF_A_KIND,  # 30 (sum)
                Box.FOUR_OF_A_KIND,  # 30 (sum)
                Box.CHANCE,  # 30 (sum)
            ]
            face_cycle = [1, 2, 3, 4, 5, 6]
            for box, face in zip(lower_boxes, face_cycle):
                card.set_box_score(box, DiceRoll([face] * 5))

            # Final assertion
            self.assertEqual(
                card.get_card_score(),
                1575,
                f"Expected 1575, got {card.get_card_score()}",
            )


if __name__ == "__main__":
    unittest.main()
