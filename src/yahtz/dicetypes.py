# src/yaht/dice.py
from collections import Counter
from random import randint
from typing import Any, Iterator

from yahtz.boxes import Box, Section
from yahtz.exceptions import (
    DiceCountError,
    DiceRollCountError,
    DieValueError,
)

MAX_ROLL_COUNT = 3


class DiceCup:
    def __init__(self):
        self._roll_count = 0
        self._stored_roll: DiceRoll | None = None

    def roll_dice(self, reroll_indices: list[int] | None = None) -> "DiceRoll":
        # Manage roll cup lifecycle
        self._roll_count += 1
        if self._roll_count > MAX_ROLL_COUNT:
            raise DiceRollCountError()

        # Do full dice first time through or if no/None indices specified
        if self._stored_roll is None or not reroll_indices:
            self._stored_roll = DiceRoll()
            return DiceRoll(self._stored_roll.numbers)  # copy for safety

        # On re-roll (with indices) do index-based reroll
        updated_numbers = self._stored_roll.numbers
        for index in reroll_indices:
            updated_numbers[index] = randint(1, 6)
        self._stored_roll = DiceRoll(updated_numbers)

        return DiceRoll(self._stored_roll.numbers)  # copy for safety

    @property
    def current_role(self) -> "DiceRoll | None":
        return None if self._stored_roll is None else DiceRoll(self._stored_roll.numbers)


class DiceRoll:
    def __init__(self, numbers: list[int] | None = None):
        """Validate dice_list in accord with Yahtzee rules and initialize class."""
        if numbers is None:
            numbers = [randint(1, 6) for _ in range(5)]

        # Check if we have exactly 5 dice
        if len(numbers) != 5:
            raise DiceCountError(f"Invalid dice count: {len(numbers)}")

        # Check if all dice values are between 1 and 6
        if any(d < 1 or d > 6 for d in numbers):
            raise DieValueError("The value of all dice must be between 1 and 6.")

        # Copy to avoid risk that dice_list argument is later mutated by caller
        self._numbers = numbers.copy()

    def __repr__(self) -> str:
        """Return string representation of the dice roll."""
        return f"DiceRoll({self._numbers})"

    def __len__(self) -> int:
        """Return the number of dice (always 5 for Yahtzee)."""
        return len(self._numbers)

    def __eq__(self, other: Any) -> bool:
        """Check equality with another DiceRoll (order independent)."""
        if not isinstance(other, DiceRoll):
            return False
        return sorted(self._numbers) == sorted(other._numbers)

    def __hash__(self) -> int:
        """Make DiceRoll hashable (useful for sets/dicts)."""
        return hash(tuple(sorted(self._numbers)))

    def __contains__(self, element: Any) -> bool:
        if isinstance(element, int):
            return element in self._numbers

        if not isinstance(element, Box):
            return False

        if element.section == Section.UPPER or element == Box.CHANCE:
            return True  # These boxes are unconstrained (apart from joker rules)

        number_counts = Counter(self._numbers).values()
        sorted_numbers = sorted(self._numbers)

        if element == Box.THREE_OF_A_KIND:
            return max(number_counts) >= 3

        if element == Box.FOUR_OF_A_KIND:
            return max(number_counts) >= 4

        if element == Box.FULL_HOUSE:
            return sorted(number_counts) in [[2, 3], [5]]

        if element == Box.SMALL_STRAIGHT:
            straights = [{1, 2, 3, 4}, {2, 3, 4, 5}, {3, 4, 5, 6}]
            return any(set(self._numbers).issuperset(s) for s in straights)

        if element == Box.LARGE_STRAIGHT:
            return sorted_numbers in [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6]]

        if element == Box.YAHTZEE:
            return max(number_counts) == 5

        return False

    def __getitem__(self, index: int) -> int:
        """Get number at specified index."""
        return self._numbers[index]

    def __iter__(self) -> Iterator[int]:
        """Iterate over dice numbers."""
        return iter(self._numbers)

    @property
    def numbers(self) -> list[int]:
        """Return a copy of the dice numbers list."""
        return self._numbers.copy()
