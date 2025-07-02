# src/yahtz/cliplayer.py
from tabulate import tabulate

from yahtz.boxes import Box
from yahtz.dicetypes import DiceRoll
from yahtz.game import PlayerGameState
from yahtz.scorecheck import calculate_score


class CLIPlayer:
    """Interactive command-line player implementation."""

    def __init__(self, name: str = "Human"):
        self.name = name

    def take_turn(self, state: PlayerGameState) -> Box:
        """Interactive turn implementation allowing user to roll dice and choose scoring box."""
        print(f"\n{self.name}'s turn!")
        self._display_scorecard(state)

        dice_to_reroll = []

        for roll_count in range(1, 4):
            roll = state.dice_cup.roll_dice(reroll_indices=dice_to_reroll)
            self._display_dice(roll_count, roll)

            # Check if user wants to end turn or continue rolling
            if roll_count < 3:
                if self._should_end_turn():
                    break
                dice_to_reroll = self._get_reroll_choice()

        return self._choose_scoring_box(roll, state)  # type: ignore

    def _display_scorecard(self, state: PlayerGameState) -> None:
        """Display current scorecard state."""

        def names_and_scores(boxes: list[Box]) -> tuple[list[str], list[str]]:
            names = [box.name for box in boxes]
            scores = [str(state.card.box_scores.get(box) or "---") for box in boxes]
            return names, scores

        upr_names, upr_scores = names_and_scores(Box.get_upper_boxes())
        upr_names.append("Upr Total")
        upr_scores.append(
            str(sum(state.card.box_scores[box] or 0 for box in Box.get_upper_boxes()))
        )
        lwr_names, lwr_scores = names_and_scores(Box.get_lower_boxes())

        grid = [upr_names, upr_scores, lwr_names, lwr_scores]
        print(tabulate(grid, tablefmt="simple_grid"))
        print(f"Total Score: {state.card.get_card_score()}")

    def _display_dice(self, roll_count: int, roll: DiceRoll) -> None:
        """Display current dice roll."""
        dice_str = " ".join(f"[{die}]" for die in roll.numbers)
        print(f"\n--- Roll {roll_count}: {dice_str} ---")

    def _should_end_turn(self) -> bool:
        """Ask user if they want to end their turn."""
        while True:
            choice = input("Do you want to (r)oll again or (s)core? ").lower().strip()
            if choice in ["r", "roll"]:
                return False
            elif choice in ["s", "score"]:
                return True
            else:
                print("Please enter 'r' for roll or 's' for score.")

    def _get_reroll_choice(self) -> list[int]:
        """Get user's choice of which dice to reroll."""
        while True:
            choice = (
                input("Space separated reroll dice positions (1-5): ").strip().lower()
            )

            if choice == "all":
                return []

            try:
                positions = [int(x) for x in choice.split()]
                if all(1 <= pos <= 5 for pos in positions):
                    # Convert to 0-based indices
                    return [pos - 1 for pos in positions]
                else:
                    print("Please enter positions between 1 and 5.")
            except ValueError:
                print("Please enter valid numbers or 'all'.")

    def _choose_scoring_box(self, roll: DiceRoll, state: PlayerGameState) -> Box:
        """Let user choose which box to score."""
        unscored_boxes = state.card.get_unscored_boxes()

        print(f"\nFinal roll: {' '.join(f'[{die}]' for die in roll.numbers)}")
        print("\nAvailable scoring categories:")

        # Display available boxes with potential scores
        for i, box in enumerate(unscored_boxes, 1):
            potential_score = self._calculate_potential_score(box, roll)
            print(f"  {i}. {box.name} ({potential_score} points)")

        while True:
            try:
                choice = int(input(f"Choose category (1-{len(unscored_boxes)}): "))
                if 1 <= choice <= len(unscored_boxes):
                    return unscored_boxes[choice - 1]
                else:
                    print(f"Please enter a number between 1 and {len(unscored_boxes)}.")
            except ValueError:
                print("Please enter a valid number.")

    def _calculate_potential_score(self, box: Box, roll: DiceRoll) -> int:
        """Calculate potential score for a box given the current roll."""

        # For display purposes, we'll show what the score would be
        # This is a simplified version that doesn't account for all game state
        if box in roll:
            return calculate_score(box, roll)
        else:
            return 0
