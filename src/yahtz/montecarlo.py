"""montecarlo.py - Refactored for better maintainability"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from random import choices

from yahtz.boxes import Box, Section
from yahtz.dicetypes import DiceRoll
from yahtz.exceptions import InvalidBoxError
from yahtz.game import PlayerGameState
from yahtz.scorecard import ScorecardView
from yahtz.scorecheck import Scoreability, calculate_score, check_scoreability

REROLL_ALL = [0, 1, 2, 3, 4]
REROLL_NONE: list[int] = []

YZ_ASSIST_BONUS = 100
YZ_PROPER_BONUS = 100
UPPER_SCORE_BONUS = 35


# def structify(tuple_data: tuple[Any, ...], *field_names: str) -> SimpleNamespace:
#     """Quick and dirty named-tuple-like maker when formal NamedTuple is overkill."""
#     return SimpleNamespace(dict(zip(field_names, tuple_data)))


@dataclass
class Analysis:
    """Per box simulation result used for end of roll decision making."""

    occurrences: int = 0  # Number of times box was scored for points
    mean_score: float = 0.0  # Average score across occurrences
    probability: float = 0.0  # Occurrences / reroll trials
    expected_score: float = 0.0  # Mean score multiplied by


@dataclass
class Expected:
    """Convenience struct to associate expected_score from analysis with box."""

    box: Box
    expected_score: float


@dataclass
class TurnDecision:
    """Encapsulates information associated with ending/rerolling w/in a turn."""

    best_box: Box  # Highest expected scoring box from last roll
    should_end_turn: bool  # True if no reroll needed for out of rolls
    dice_to_reroll: list[int]  # Reroll indices for best_box next roll


class RerollStrategy:
    """Handles dice reroll logic for different box types."""

    EV = 3.5  # Expected value of a single rolled die

    def choose_dice_to_reroll(self, box: Box, roll: DiceRoll) -> list[int]:
        """Determine which dice to reroll to maximize box score."""
        counts: Counter[int] = Counter(roll.numbers)
        most_common = counts.most_common(1)[0]

        match box:
            case Box.THREE_OF_A_KIND | Box.FOUR_OF_A_KIND:
                return self._kind_strategy(box, roll, most_common)
            case Box.FULL_HOUSE:
                return self._full_house_strategy(roll, counts, most_common)
            case Box.SMALL_STRAIGHT | Box.LARGE_STRAIGHT:
                return self._straight_strategy(box, roll)
            case Box.YAHTZEE:
                return self._yahtzee_strategy(roll, counts)
            case Box.CHANCE:
                return self._chance_strategy(roll)
            case _ if box.section == Section.UPPER:
                return self._upper_strategy(box, roll, counts)
            case _:
                raise InvalidBoxError(f"No strategy defined for box: {box.name}")

        raise InvalidBoxError(f"No strategy defined for box: {box.name}")

    def _upper_strategy(
        self, box: Box, roll: DiceRoll, counts: Counter[int]
    ) -> list[int]:
        """Reroll strategy selection for all upper section boxes."""

        if box.die_number is None:
            raise InvalidBoxError(f"Expected upper box not: {box.name}")

        box_number = box.die_number
        # If more than zero box_numbers in roll, reroll others
        if counts[box_number] > 0:
            return [i for i in range(5) if roll[i] != box_number]
        # If no box numbers in roll, reroll everything
        return REROLL_ALL

    def _kind_strategy(
        self, box: Box, roll: DiceRoll, most_common: tuple[int, int]
    ) -> list[int]:
        """Strategy for three/four of a kind."""
        keeper_target = 3 if box == Box.THREE_OF_A_KIND else 4
        number, kind = most_common

        if kind == 1:  # No matching numbers, so reroll all but highest
            if (max_number := max(roll)) > self.EV:
                return [i for i in range(5) if roll[i] != max_number]
            return REROLL_ALL  # Reroll all if highest is not very high
        elif kind < keeper_target:  # Build on matches in roll
            return [i for i in range(5) if roll[i] != number]
        else:  # If a winner, reroll non-matching "lows" to maximize sum-all scoring
            return [i for i in range(5) if roll[i] != number and roll[i] < self.EV]

    def _full_house_strategy(
        self, roll: DiceRoll, counts: Counter[int], most_common: tuple[int, int]
    ) -> list[int]:
        """Strategy for full house."""
        if Box.FULL_HOUSE in roll:
            return REROLL_NONE

        number, kind = most_common
        # If 2 kind, look for a second 2 kind and reroll outlier
        if kind == 2:
            two_most_common = counts.most_common(2)
            second_number, second_kind = two_most_common[1]
            if second_kind == 2:
                return [i for i in range(5) if roll[i] not in [number, second_number]]
            # If only a single 2 kind, reroll everything else
            return [i for i in range(5) if roll[i] != number]
        # If 3 or 4 kind, take one for the team and try to max it
        elif 3 <= kind <= 4:
            return [i for i in range(5) if roll[i] != number]
        # If nothing of interest, give up
        else:
            return REROLL_ALL

    def _straight_strategy(self, box: Box, roll: DiceRoll) -> list[int]:
        """Strategy for small/large straights."""
        if box in roll:
            return REROLL_NONE

        patterns: dict[Box, list[list[int]]] = {
            Box.SMALL_STRAIGHT: [[1, 2, 3, 4], [2, 3, 4, 5], [3, 4, 5, 6]],
            Box.LARGE_STRAIGHT: [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6]],
        }

        best_match = max(patterns[box], key=lambda x: len(set(x).intersection(roll)))
        seen: set[int] = set()
        dice_to_reroll: list[int] = []

        for idx, number in enumerate(roll):
            if number not in best_match or number in seen:
                dice_to_reroll.append(idx)
            seen.add(number)

        return dice_to_reroll

    def _yahtzee_strategy(self, roll: DiceRoll, counts: Counter[int]) -> list[int]:
        """Strategy for Yahtzee."""
        if Box.YAHTZEE in roll:
            return REROLL_NONE

        first, second = counts.most_common(2)
        if first[1] == second[1]:  # if 2 pair, keep pair that scores more
            keeper_number = first[0] if first[1] > second[1] else second[1]
        else:  # Otherwise, keep what we have the most of
            keeper_number = first[0]

        return [i for i in range(5) if roll[i] != keeper_number]

    def _chance_strategy(self, roll: DiceRoll) -> list[int]:
        """Strategy for chance."""
        return [i for i in range(5) if roll[i] < self.EV]  # Reroll anything "low"


class ScoreCalculator:
    """Handles score calculations and bonuses."""

    @staticmethod
    def calculate_trial_scores(
        unscored_boxes: list[Box],
        roll: DiceRoll,
        card: ScorecardView,
        upper_score: int | None = None,
    ) -> dict[int, list[Box]]:
        """Calculate scores for all unscored boxes for a single trial."""
        trial_scores: defaultdict[int, list[Box]] = defaultdict(list)
        if upper_score is None:
            upper_score = ScoreCalculator.calculate_upper_score(card)

        for box in unscored_boxes:
            score = ScoreCalculator._calculate_box_score(box, roll, card, upper_score)
            if score is not None:
                trial_scores[score].append(box)

        return trial_scores

    @staticmethod
    def calculate_upper_score(card: ScorecardView) -> int:
        """Get current upper section score."""
        return sum(card.box_scores[box] or 0 for box in Box.get_upper_boxes())

    @staticmethod
    def _calculate_box_score(
        box: Box, roll: DiceRoll, card: ScorecardView, upper_score: int
    ) -> int | None:
        """Calculate score for a specific box including bonuses."""
        scoreability = check_scoreability(box, roll, card)
        if scoreability == Scoreability.NOT_SCOREABLE:
            return None

        score = (
            calculate_score(box, roll)
            if scoreability == Scoreability.POINTS_SCOREABLE
            else 0
        )

        # Add bonuses
        score += ScoreCalculator._calculate_yahtzee_bonus(roll, card)
        score += ScoreCalculator._calculate_upper_bonus(box, score, upper_score)

        return score

    @staticmethod
    def _calculate_yahtzee_bonus(roll: DiceRoll, card: ScorecardView) -> int:
        """Calculate Yahtzee bonus if applicable."""
        score = 0
        if Box.YAHTZEE in roll:
            match card.box_scores[Box.YAHTZEE]:
                case None:
                    score = YZ_ASSIST_BONUS  # Experimental "Yahtzee Assist"
                case 50:
                    score = YZ_PROPER_BONUS  # Yahtzee bonus rule in action
                case _:
                    score = 0
        return score

    @staticmethod
    def _calculate_upper_bonus(box: Box, score: int, upper_score: int) -> int:
        """Calculate upper section bonus if applicable."""
        if (
            box.section == Section.UPPER
            and upper_score < 63
            and upper_score + score >= 63
        ):
            return UPPER_SCORE_BONUS
        return 0


class SimulationEngine:
    """Handles Monte Carlo simulations."""

    def __init__(self, score_calculator: ScoreCalculator):
        self.score_calculator = score_calculator

    def simulate_rolls(
        self,
        state: PlayerGameState,
        roll: DiceRoll,
        reroll_indices: list[int],
        trials: int,
    ) -> dict[Box, Analysis]:
        """Simulate dice rolls and return analysis of outcomes."""
        keepers, keepers_count = self._prepare_keepers(roll, reroll_indices)
        unscored_boxes = state.card.get_unscored_boxes()
        upper_score = ScoreCalculator.calculate_upper_score(state.card)

        occurrences: defaultdict[Box, int] = defaultdict(int)
        total_scores: defaultdict[Box, int] = defaultdict(int)

        # Optimize for no rerolls case
        if keepers_count == 5:
            return self._analyze_no_reroll(unscored_boxes, roll, state.card, trials)

        # Pre-generate random rolls for efficiency
        reroll_batch = self._generate_reroll_batch(keepers_count, trials)

        # Run simulation trials
        for trial_idx in range(trials):
            simulated_roll = self._create_simulated_roll(keepers, reroll_batch[trial_idx])
            trial_scores = self.score_calculator.calculate_trial_scores(
                unscored_boxes, simulated_roll, state.card, upper_score
            )

            self._update_trial_statistics(trial_scores, occurrences, total_scores)

        return self._build_analysis(unscored_boxes, occurrences, total_scores, trials)

    def _prepare_keepers(
        self, roll: DiceRoll, reroll_indices: list[int]
    ) -> tuple[list[int], int]:
        """Extract keeper dice and count."""
        keepers = [roll[i] for i in range(5) if i not in reroll_indices]
        return keepers, len(keepers)

    def _generate_reroll_batch(self, keepers_count: int, trials: int) -> list[list[int]]:
        """Pre-generate random dice for efficiency."""
        return [choices([1, 2, 3, 4, 5, 6], k=5 - keepers_count) for _ in range(trials)]

    def _create_simulated_roll(self, keepers: list[int], new_dice: list[int]) -> DiceRoll:
        """Create a simulated roll combining keepers and new dice."""
        simroll_numbers = keepers + new_dice
        return DiceRoll(simroll_numbers)

    def _update_trial_statistics(
        self,
        trial_scores: dict[int, list[Box]],
        occurrences: dict[Box, int],
        total_scores: dict[Box, int],
    ):
        """Update occurrence and score statistics from a trial."""
        if trial_scores:
            high_score = max(trial_scores)
            for box in trial_scores[high_score]:
                occurrences[box] += 1
                total_scores[box] += high_score

    def _analyze_no_reroll(
        self, unscored_boxes: list[Box], roll: DiceRoll, card: ScorecardView, trials: int
    ) -> dict[Box, Analysis]:
        """Handle special case where no rerolls are needed."""
        trial_scores = self.score_calculator.calculate_trial_scores(
            unscored_boxes, roll, card
        )
        occurrences: dict[Box, int] = defaultdict(int)
        total_scores: dict[Box, int] = defaultdict(int)

        if trial_scores:
            high_score = max(trial_scores)
            for box in trial_scores[high_score]:
                occurrences[box] = trials
                total_scores[box] = high_score * trials

        return self._build_analysis(unscored_boxes, occurrences, total_scores, trials)

    def _build_analysis(
        self,
        unscored_boxes: list[Box],
        occurrences: dict[Box, int],
        total_scores: dict[Box, int],
        trials: int,
    ) -> dict[Box, Analysis]:
        """Build final analysis from simulation results."""
        analysis: dict[Box, Analysis] = {}
        for box in unscored_boxes:
            if occurrences[box] > 0:
                mean_score = total_scores[box] / occurrences[box]
                probability = occurrences[box] / trials
                analysis[box] = Analysis(
                    occurrences=occurrences[box],
                    mean_score=mean_score,
                    probability=probability,
                    expected_score=probability * mean_score,
                )
        return analysis


class TurnManager:
    """Manages turn logic and decision making."""

    def __init__(
        self,
        reroll_strategy: RerollStrategy,
        simulation_engine: SimulationEngine,
        trials: int,
    ):
        self.reroll_strategy = reroll_strategy
        self.simulation_engine = simulation_engine
        self.trials = trials

    def make_turn_decision(
        self, state: PlayerGameState, roll: DiceRoll, roll_count: int
    ) -> TurnDecision:
        """Make a decision for the current turn state."""
        unscored_boxes = state.card.get_unscored_boxes()

        if roll_count == 3:  # Final roll
            return self._make_final_decision(unscored_boxes, roll, state.card)

        # Calculate reroll strategies for all boxes
        reroll_strategies = self._calculate_reroll_strategies(unscored_boxes, roll)

        # Simulate and find best expected outcome
        expected_results = self._simulate_strategies(state, roll, reroll_strategies)

        if not expected_results:
            # Fallback to best available score
            return self._make_final_decision(unscored_boxes, roll, state.card)

        best_expected = max(expected_results, key=lambda e: e.expected_score)
        dice_to_reroll = reroll_strategies[best_expected.box]

        return TurnDecision(
            best_box=best_expected.box,
            should_end_turn=len(dice_to_reroll) == 0,
            dice_to_reroll=dice_to_reroll,
        )

    def _calculate_reroll_strategies(
        self, unscored_boxes: list[Box], roll: DiceRoll
    ) -> dict[Box, list[int]]:
        """Calculate reroll strategy for each unscored box."""
        return {
            box: self.reroll_strategy.choose_dice_to_reroll(box, roll)
            for box in unscored_boxes
        }

    def _simulate_strategies(
        self, state: PlayerGameState, roll: DiceRoll, strategies: dict[Box, list[int]]
    ) -> list[Expected]:
        """Simulate each reroll strategy and return expected results."""
        expected_results: list[Expected] = []

        for box, reroll_indices in strategies.items():
            analysis = self.simulation_engine.simulate_rolls(
                state, roll, reroll_indices, self.trials
            )
            if box in analysis:
                expected_results.append(Expected(box, analysis[box].expected_score))

        return expected_results

    def _make_final_decision(
        self, unscored_boxes: list[Box], roll: DiceRoll, card: ScorecardView
    ) -> TurnDecision:
        """Make final decision when no more rolls are available."""
        score_calculator = ScoreCalculator()
        boxes_by_score = score_calculator.calculate_trial_scores(
            unscored_boxes, roll, card
        )

        if boxes_by_score:
            high_score = max(boxes_by_score)
            best_box = boxes_by_score[high_score][0]
        else:
            # Fallback if no scoreable boxes
            best_box = unscored_boxes[0]

        return TurnDecision(best_box=best_box, should_end_turn=True, dice_to_reroll=[])


class MonteCarloBot:
    """Player protocol implementation using probabilistic strategies."""

    def __init__(self, name: str = "Monte", trials: int = 75):
        self.name = name
        self.trials = trials

        # Initialize components
        self.reroll_strategy = RerollStrategy()
        self.score_calculator = ScoreCalculator()
        self.simulation_engine = SimulationEngine(self.score_calculator)
        self.turn_manager = TurnManager(
            self.reroll_strategy, self.simulation_engine, trials
        )

    def take_turn(self, state: PlayerGameState) -> Box:
        """Called by Game when it is time for Player to take a turn."""
        dice_to_reroll = []

        for roll_count in range(1, 4):
            roll = state.dice_cup.roll_dice(reroll_indices=dice_to_reroll)

            decision = self.turn_manager.make_turn_decision(state, roll, roll_count)

            if decision.should_end_turn:
                return decision.best_box

            dice_to_reroll = decision.dice_to_reroll

        raise RuntimeError("Turn should have ended by roll 3")
