import unittest

# tests/test_dicecup.py
from unittest.mock import patch

from yahtz.boxes import Box
from yahtz.dicetypes import MAX_ROLL_COUNT, DiceCup, DiceRoll
from yahtz.exceptions import DiceRollCountError


class TestDiceCup(unittest.TestCase):
    def test_first_roll_generates_dice_roll(self):
        cup = DiceCup()
        roll = cup.roll_dice()
        self.assertIsInstance(roll, DiceRoll)
        self.assertEqual(len(roll), 5)
        for die in roll:
            self.assertIn(die, range(1, 7))

    def test_reroll_changes_specified_dice_only(self):
        with patch("yahtz.dicetypes.randint", side_effect=[2, 3, 4, 5, 6, 1, 1]):
            cup = DiceCup()
            _ = cup.roll_dice()
            # Initial should be [2, 3, 4, 5, 6]
            rerolled = cup.roll_dice(reroll_indices=[0, 1])
            # Next two values in mock: [1, 1] should replace indices 0 and 1
            expected = [1, 1, 4, 5, 6]
            self.assertEqual(rerolled.numbers, expected)

    def test_roll_limit_raises_error(self):
        cup = DiceCup()
        for _ in range(MAX_ROLL_COUNT):
            cup.roll_dice()
        with self.assertRaises(DiceRollCountError):
            cup.roll_dice()

    def test_roll_isolated_from_mutation(self):
        cup = DiceCup()
        roll = cup.roll_dice()
        roll.numbers[0] = 42  # attempt mutation on copy
        self.assertNotEqual(cup.current_role.numbers[0], 42)

    def test_current_role_returns_copy(self):
        cup = DiceCup()
        roll1 = cup.roll_dice()
        roll2 = cup.current_role
        self.assertIsInstance(roll2, DiceRoll)
        self.assertEqual(roll1, roll2)
        self.assertIsNot(roll1, roll2)  # ensure it's a copy

    def test_current_role_is_none_before_first_roll(self):
        self.assertIsNone(DiceCup().current_role)


if __name__ == "__main__":
    unittest.main()


class TestDiceRollInitialization(unittest.TestCase):
    """Test DiceRoll initialization and validation."""

    def test_valid_dice_roll(self):
        """Test creating a valid dice roll."""
        dice = DiceRoll([1, 2, 3, 4, 5])
        self.assertEqual(dice.numbers, [1, 2, 3, 4, 5])

    def test_valid_dice_roll_with_duplicates(self):
        """Test creating a valid dice roll with duplicate values."""
        dice = DiceRoll([1, 1, 1, 1, 1])
        self.assertEqual(dice.numbers, [1, 1, 1, 1, 1])

    def test_invalid_dice_count_too_few(self):
        """Test error when fewer than 5 dice provided."""
        with self.assertRaises(Exception):
            DiceRoll([1, 2, 3, 4])
        # self.assertEqual(str(cm.exception), "Invalid dice count: 4")

    def test_invalid_dice_count_too_many(self):
        """Test error when more than 5 dice provided."""
        with self.assertRaises(Exception):
            DiceRoll([1, 2, 3, 4, 5, 6])
        # self.assertEqual(str(cm.exception), "Invalid dice count: 6")

    def test_invalid_dice_count_empty(self):
        """Test error when empty dice list provided."""
        with self.assertRaises(Exception):
            DiceRoll([])
        # self.assertEqual(str(cm.exception), "Invalid dice count: 0")

    def test_invalid_die_value_too_low(self):
        """Test error when die value is below 1."""
        with self.assertRaises(Exception):
            DiceRoll([0, 2, 3, 4, 5])
        # self.assertEqual(str(cm.exception), "The value of all dice must be between 1 and 6.")

    def test_invalid_die_value_too_high(self):
        """Test error when die value is above 6."""
        with self.assertRaises(Exception):
            DiceRoll([1, 2, 3, 4, 7])
        # self.assertEqual(str(cm.exception), "The value of all dice must be between 1 and 6.")

    def test_invalid_die_value_negative(self):
        """Test error when die value is negative."""
        with self.assertRaises(Exception):
            DiceRoll([-1, 2, 3, 4, 5])
        # self.assertEqual(str(cm.exception), "The value of all dice must be between 1 and 6.")

    def test_multiple_invalid_die_values(self):
        """Test error when multiple die values are invalid."""
        with self.assertRaises(Exception):
            DiceRoll([0, 2, 3, 4, 8])

    def test_immutable_input_list(self):
        """Test that original input list is not affected by mutations."""
        original = [1, 2, 3, 4, 5]
        dice = DiceRoll(original)
        original[0] = 6  # Mutate original list
        self.assertEqual(dice.numbers, [1, 2, 3, 4, 5])  # Should be unchanged


class TestDiceRollProperties(unittest.TestCase):
    """Test DiceRoll properties and basic operations."""

    def setUp(self):
        self.dice = DiceRoll([1, 2, 3, 4, 5])

    def test_numbers_property_returns_copy(self):
        """Test that numbers property returns a copy, not reference."""
        numbers = self.dice.numbers
        numbers[0] = 6
        self.assertEqual(self.dice.numbers, [1, 2, 3, 4, 5])

    def test_len(self):
        """Test length of dice roll."""
        self.assertEqual(len(self.dice), 5)

    def test_repr(self):
        """Test string representation."""
        self.assertEqual(repr(self.dice), "DiceRoll([1, 2, 3, 4, 5])")

    def test_getitem(self):
        """Test indexing into dice roll."""
        self.assertEqual(self.dice[0], 1)
        self.assertEqual(self.dice[4], 5)

    def test_getitem_negative_index(self):
        """Test negative indexing."""
        self.assertEqual(self.dice[-1], 5)
        self.assertEqual(self.dice[-5], 1)

    def test_getitem_out_of_bounds(self):
        """Test index out of bounds error."""
        with self.assertRaises(IndexError):
            _ = self.dice[5]

    def test_iter(self):
        """Test iteration over dice."""
        result = list(self.dice)
        self.assertEqual(result, [1, 2, 3, 4, 5])

    def test_iter_for_loop(self):
        """Test iteration in for loop."""
        values: list[int] = []
        for die in self.dice:
            values.append(die)
        self.assertEqual(values, [1, 2, 3, 4, 5])


class TestDiceRollEquality(unittest.TestCase):
    """Test DiceRoll equality and hashing."""

    def test_equality_same_order(self):
        """Test equality with same order."""
        dice1 = DiceRoll([1, 2, 3, 4, 5])
        dice2 = DiceRoll([1, 2, 3, 4, 5])
        self.assertEqual(dice1, dice2)

    def test_equality_different_order(self):
        """Test equality with different order (should be equal)."""
        dice1 = DiceRoll([1, 2, 3, 4, 5])
        dice2 = DiceRoll([5, 4, 3, 2, 1])
        self.assertEqual(dice1, dice2)

    def test_equality_with_duplicates(self):
        """Test equality with duplicate values."""
        dice1 = DiceRoll([1, 1, 2, 2, 3])
        dice2 = DiceRoll([2, 1, 3, 2, 1])
        self.assertEqual(dice1, dice2)

    def test_inequality(self):
        """Test inequality."""
        dice1 = DiceRoll([1, 2, 3, 4, 5])
        dice2 = DiceRoll([1, 2, 3, 4, 6])
        self.assertNotEqual(dice1, dice2)

    def test_equality_with_non_dice_roll(self):
        """Test equality with non-DiceRoll object."""
        dice = DiceRoll([1, 2, 3, 4, 5])
        self.assertNotEqual(dice, [1, 2, 3, 4, 5])
        self.assertNotEqual(dice, "DiceRoll([1, 2, 3, 4, 5])")
        self.assertNotEqual(dice, None)

    def test_hash_same_dice(self):
        """Test that same dice have same hash."""
        dice1 = DiceRoll([1, 2, 3, 4, 5])
        dice2 = DiceRoll([5, 4, 3, 2, 1])
        self.assertEqual(hash(dice1), hash(dice2))

    def test_hash_different_dice(self):
        """Test that different dice have different hash."""
        dice1 = DiceRoll([1, 2, 3, 4, 5])
        dice2 = DiceRoll([1, 2, 3, 4, 6])
        self.assertNotEqual(hash(dice1), hash(dice2))

    def test_dice_in_set(self):
        """Test that DiceRoll can be used in sets."""
        dice1 = DiceRoll([1, 2, 3, 4, 5])
        dice2 = DiceRoll([5, 4, 3, 2, 1])  # Same dice, different order
        dice3 = DiceRoll([1, 2, 3, 4, 6])

        dice_set = {dice1, dice2, dice3}
        self.assertEqual(len(dice_set), 2)  # dice1 and dice2 are equal

    def test_dice_as_dict_key(self):
        """Test that DiceRoll can be used as dictionary key."""
        dice1 = DiceRoll([1, 2, 3, 4, 5])
        dice2 = DiceRoll([5, 4, 3, 2, 1])

        dice_dict = {dice1: "first"}
        dice_dict[dice2] = "second"  # Should overwrite first entry

        self.assertEqual(len(dice_dict), 1)
        self.assertEqual(dice_dict[dice1], "second")


class TestDiceRollContainsInteger(unittest.TestCase):
    """Test DiceRoll contains method with integers."""

    def test_contains_existing_value(self):
        """Test checking for existing die value."""
        dice = DiceRoll([1, 2, 3, 4, 5])
        self.assertIn(1, dice)
        self.assertIn(3, dice)
        self.assertIn(5, dice)

    def test_contains_non_existing_value(self):
        """Test checking for non-existing die value."""
        dice = DiceRoll([1, 2, 3, 4, 5])
        self.assertNotIn(6, dice)

    def test_contains_with_duplicates(self):
        """Test contains with duplicate values."""
        dice = DiceRoll([1, 1, 2, 2, 3])
        self.assertIn(1, dice)
        self.assertIn(2, dice)
        self.assertIn(3, dice)
        self.assertNotIn(4, dice)


class TestDiceRollContainsUpperBoxes(unittest.TestCase):
    """Test DiceRoll contains method with upper section boxes."""

    def test_contains_upper_boxes(self):
        """Test that all upper boxes are always valid."""
        dice = DiceRoll([1, 2, 3, 4, 5])

        for box in Box.get_upper_boxes():
            with self.subTest(box=box):
                self.assertIn(box, dice)

    def test_contains_chance(self):
        """Test that CHANCE box is always valid."""
        dice = DiceRoll([1, 2, 3, 4, 5])
        self.assertIn(Box.CHANCE, dice)


class TestDiceRollContainsThreeOfAKind(unittest.TestCase):
    """Test DiceRoll contains method with THREE_OF_A_KIND box."""

    def test_three_of_a_kind_valid(self):
        """Test valid three of a kind."""
        dice = DiceRoll([1, 1, 1, 2, 3])
        self.assertIn(Box.THREE_OF_A_KIND, dice)

    def test_three_of_a_kind_with_four(self):
        """Test three of a kind with four matching dice."""
        dice = DiceRoll([2, 2, 2, 2, 3])
        self.assertIn(Box.THREE_OF_A_KIND, dice)

    def test_three_of_a_kind_with_five(self):
        """Test three of a kind with five matching dice (Yahtzee)."""
        dice = DiceRoll([3, 3, 3, 3, 3])
        self.assertIn(Box.THREE_OF_A_KIND, dice)

    def test_three_of_a_kind_invalid(self):
        """Test invalid three of a kind."""
        dice = DiceRoll([1, 2, 3, 4, 5])
        self.assertNotIn(Box.THREE_OF_A_KIND, dice)

    def test_three_of_a_kind_with_pairs(self):
        """Test three of a kind with only pairs."""
        dice = DiceRoll([1, 1, 2, 2, 3])
        self.assertNotIn(Box.THREE_OF_A_KIND, dice)


class TestDiceRollContainsFourOfAKind(unittest.TestCase):
    """Test DiceRoll contains method with FOUR_OF_A_KIND box."""

    def test_four_of_a_kind_valid(self):
        """Test valid four of a kind."""
        dice = DiceRoll([1, 1, 1, 1, 2])
        self.assertIn(Box.FOUR_OF_A_KIND, dice)

    def test_four_of_a_kind_with_five(self):
        """Test four of a kind with five matching dice (Yahtzee)."""
        dice = DiceRoll([3, 3, 3, 3, 3])
        self.assertIn(Box.FOUR_OF_A_KIND, dice)

    def test_four_of_a_kind_invalid_three(self):
        """Test invalid four of a kind with only three matching."""
        dice = DiceRoll([1, 1, 1, 2, 3])
        self.assertNotIn(Box.FOUR_OF_A_KIND, dice)

    def test_four_of_a_kind_invalid_no_match(self):
        """Test invalid four of a kind with no matches."""
        dice = DiceRoll([1, 2, 3, 4, 5])
        self.assertNotIn(Box.FOUR_OF_A_KIND, dice)


class TestDiceRollContainsFullHouse(unittest.TestCase):
    """Test DiceRoll contains method with FULL_HOUSE box."""

    def test_full_house_valid(self):
        """Test valid full house (3 of one, 2 of another)."""
        dice = DiceRoll([1, 1, 1, 2, 2])
        self.assertIn(Box.FULL_HOUSE, dice)

    def test_full_house_valid_reverse(self):
        """Test valid full house (2 of one, 3 of another)."""
        dice = DiceRoll([1, 1, 2, 2, 2])
        self.assertIn(Box.FULL_HOUSE, dice)

    def test_full_house_with_yahtzee(self):
        """Test full house with Yahtzee (5 of a kind counts as full house)."""
        dice = DiceRoll([3, 3, 3, 3, 3])
        self.assertIn(Box.FULL_HOUSE, dice)

    def test_full_house_invalid_three_only(self):
        """Test invalid full house with only three of a kind."""
        dice = DiceRoll([1, 1, 1, 2, 3])
        self.assertNotIn(Box.FULL_HOUSE, dice)

    def test_full_house_invalid_no_matches(self):
        """Test invalid full house with no matches."""
        dice = DiceRoll([1, 2, 3, 4, 5])
        self.assertNotIn(Box.FULL_HOUSE, dice)

    def test_full_house_invalid_four_of_kind(self):
        """Test invalid full house with four of a kind (but not Yahtzee)."""
        dice = DiceRoll([1, 1, 1, 1, 2])
        self.assertNotIn(Box.FULL_HOUSE, dice)


class TestDiceRollContainsSmallStraight(unittest.TestCase):
    """Test DiceRoll contains method with SMALL_STRAIGHT box."""

    def test_small_straight_1234(self):
        """Test small straight 1-2-3-4."""
        dice = DiceRoll([1, 2, 3, 4, 6])
        self.assertIn(Box.SMALL_STRAIGHT, dice)

    def test_small_straight_2345(self):
        """Test small straight 2-3-4-5."""
        dice = DiceRoll([2, 3, 4, 5, 1])
        self.assertIn(Box.SMALL_STRAIGHT, dice)

    def test_small_straight_3456(self):
        """Test small straight 3-4-5-6."""
        dice = DiceRoll([3, 4, 5, 6, 1])
        self.assertIn(Box.SMALL_STRAIGHT, dice)

    def test_small_straight_with_duplicate(self):
        """Test small straight with duplicate (should still work)."""
        dice = DiceRoll([1, 2, 3, 4, 4])
        self.assertIn(Box.SMALL_STRAIGHT, dice)

    def test_small_straight_large_straight(self):
        """Test that large straight contains small straight."""
        dice = DiceRoll([1, 2, 3, 4, 5])
        self.assertIn(Box.SMALL_STRAIGHT, dice)

    def test_small_straight_invalid(self):
        """Test invalid small straight."""
        dice = DiceRoll([1, 1, 1, 1, 1])
        self.assertNotIn(Box.SMALL_STRAIGHT, dice)

    def test_small_straight_gap(self):
        """Test invalid small straight with gap."""
        dice = DiceRoll([1, 2, 2, 5, 6])
        self.assertNotIn(Box.SMALL_STRAIGHT, dice)


class TestDiceRollContainsLargeStraight(unittest.TestCase):
    """Test DiceRoll contains method with LARGE_STRAIGHT box."""

    def test_large_straight_12345(self):
        """Test large straight 1-2-3-4-5."""
        dice = DiceRoll([1, 2, 3, 4, 5])
        self.assertIn(Box.LARGE_STRAIGHT, dice)

    def test_large_straight_23456(self):
        """Test large straight 2-3-4-5-6."""
        dice = DiceRoll([2, 3, 4, 5, 6])
        self.assertIn(Box.LARGE_STRAIGHT, dice)

    def test_large_straight_unordered(self):
        """Test large straight in different order."""
        dice = DiceRoll([5, 1, 4, 2, 3])
        self.assertIn(Box.LARGE_STRAIGHT, dice)

    def test_large_straight_invalid_duplicate(self):
        """Test invalid large straight with duplicate."""
        dice = DiceRoll([1, 2, 3, 4, 4])
        self.assertNotIn(Box.LARGE_STRAIGHT, dice)

    def test_large_straight_invalid_gap(self):
        """Test invalid large straight with gap."""
        dice = DiceRoll([1, 2, 3, 5, 6])
        self.assertNotIn(Box.LARGE_STRAIGHT, dice)

    def test_large_straight_invalid_small_straight(self):
        """Test that small straight is not large straight."""
        dice = DiceRoll([1, 2, 3, 4, 6])
        self.assertNotIn(Box.LARGE_STRAIGHT, dice)


class TestDiceRollContainsYahtzee(unittest.TestCase):
    """Test DiceRoll contains method with YAHTZEE box."""

    def test_yahtzee_valid(self):
        """Test valid Yahtzee (5 of a kind)."""
        dice = DiceRoll([1, 1, 1, 1, 1])
        self.assertIn(Box.YAHTZEE, dice)

    def test_yahtzee_valid_sixes(self):
        """Test valid Yahtzee with sixes."""
        dice = DiceRoll([6, 6, 6, 6, 6])
        self.assertIn(Box.YAHTZEE, dice)

    def test_yahtzee_invalid_four(self):
        """Test invalid Yahtzee with four of a kind."""
        dice = DiceRoll([1, 1, 1, 1, 2])
        self.assertNotIn(Box.YAHTZEE, dice)

    def test_yahtzee_invalid_no_matches(self):
        """Test invalid Yahtzee with no matches."""
        dice = DiceRoll([1, 2, 3, 4, 5])
        self.assertNotIn(Box.YAHTZEE, dice)


class TestDiceRollContainsInvalidBox(unittest.TestCase):
    """Test DiceRoll contains method with invalid boxes."""

    def test_invalid_box_string(self):
        """Test that string is not treated as box."""
        dice = DiceRoll([1, 2, 3, 4, 5])

        # This should go through the integer path, not box path
        self.assertNotIn("YAHTZEE", dice)


class TestDiceRollEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def test_all_ones(self):
        """Test dice roll with all ones."""
        dice = DiceRoll([1, 1, 1, 1, 1])
        self.assertIn(Box.YAHTZEE, dice)
        self.assertIn(Box.FOUR_OF_A_KIND, dice)
        self.assertIn(Box.THREE_OF_A_KIND, dice)
        self.assertIn(Box.FULL_HOUSE, dice)

    def test_all_sixes(self):
        """Test dice roll with all sixes."""
        dice = DiceRoll([6, 6, 6, 6, 6])
        self.assertIn(Box.YAHTZEE, dice)
        self.assertIn(Box.FOUR_OF_A_KIND, dice)
        self.assertIn(Box.THREE_OF_A_KIND, dice)
        self.assertIn(Box.FULL_HOUSE, dice)

    def test_sequential_dice(self):
        """Test perfectly sequential dice."""
        dice = DiceRoll([1, 2, 3, 4, 5])
        self.assertIn(Box.LARGE_STRAIGHT, dice)
        self.assertIn(Box.SMALL_STRAIGHT, dice)
        self.assertNotIn(Box.YAHTZEE, dice)
        self.assertNotIn(Box.FOUR_OF_A_KIND, dice)
        self.assertNotIn(Box.THREE_OF_A_KIND, dice)
        self.assertNotIn(Box.FULL_HOUSE, dice)

    def test_mixed_patterns(self):
        """Test various mixed patterns."""
        test_cases = [
            (
                [1, 2, 2, 2, 3],
                [Box.THREE_OF_A_KIND],
                [Box.FOUR_OF_A_KIND, Box.YAHTZEE],
            ),
            (
                [1, 2, 2, 2, 3],
                [Box.THREE_OF_A_KIND],
                [Box.FOUR_OF_A_KIND, Box.FULL_HOUSE],
            ),
            (
                [1, 1, 1, 2, 2],
                [Box.FULL_HOUSE, Box.THREE_OF_A_KIND],
                [Box.FOUR_OF_A_KIND, Box.YAHTZEE],
            ),
        ]

        for dice_values, should_contain, should_not_contain in test_cases:
            with self.subTest(dice_values=dice_values):
                dice = DiceRoll(dice_values)

                for box in should_contain:
                    self.assertIn(box, dice, f"{box} should be in {dice_values}")

                for box in should_not_contain:
                    self.assertNotIn(box, dice, f"{box} should not be in {dice_values}")


class TestDiceRollIntegration(unittest.TestCase):
    """Integration tests combining multiple features."""

    def test_comprehensive_yahtzee_check(self):
        """Test comprehensive Yahtzee pattern checking."""
        yahtzee_dice = DiceRoll([3, 3, 3, 3, 3])

        # Should satisfy all these boxes
        expected_boxes = [
            Box.YAHTZEE,
            Box.FOUR_OF_A_KIND,
            Box.THREE_OF_A_KIND,
            Box.FULL_HOUSE,
            Box.CHANCE,
            Box.THREES,
        ]

        for box in expected_boxes:
            self.assertIn(box, yahtzee_dice)

        # Should not satisfy these
        unexpected_boxes = [
            Box.LARGE_STRAIGHT,
            Box.SMALL_STRAIGHT,
        ]

        for box in unexpected_boxes:
            self.assertNotIn(box, yahtzee_dice)

    def test_comprehensive_straight_check(self):
        """Test comprehensive straight pattern checking."""
        straight_dice = DiceRoll([1, 2, 3, 4, 5])

        # Should satisfy these boxes
        expected_boxes = [
            Box.LARGE_STRAIGHT,
            Box.SMALL_STRAIGHT,
            Box.CHANCE,
            Box.ACES,
            Box.TWOS,
            Box.THREES,
            Box.FOURS,
            Box.FIVES,
            Box.SIXES,
        ]

        for box in expected_boxes:
            self.assertIn(box, straight_dice)

        # Should not satisfy these
        unexpected_boxes = [
            Box.YAHTZEE,
            Box.FOUR_OF_A_KIND,
            Box.THREE_OF_A_KIND,
            Box.FULL_HOUSE,
        ]

        for box in unexpected_boxes:
            self.assertNotIn(box, straight_dice)

    def test_dice_roll_immutability(self):
        """Test that DiceRoll maintains immutability throughout operations."""
        original_values = [1, 2, 3, 4, 5]
        dice = DiceRoll(original_values)

        # Test various operations don't mutate internal state
        _ = list(dice)
        _ = dice.numbers
        _ = len(dice)
        _ = repr(dice)
        _ = hash(dice)
        _ = Box.YAHTZEE in dice

        # Original should be unchanged
        self.assertEqual(dice.numbers, original_values)

        # Getting numbers and modifying shouldn't affect original
        numbers = dice.numbers
        numbers.append(6)
        self.assertEqual(dice.numbers, original_values)


if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)
