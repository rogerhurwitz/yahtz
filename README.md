# yahtz

<!-- [![PyPI version](https://badge.fury.io/py/yahtz.svg)](https://badge.fury.io/py/yahtz)
[![Python Support](https://img.shields.io/pypi/pyversions/yahtz.svg)](https://pypi.org/project/yahtz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/rogerhurwitz/yahtz/workflows/CI/badge.svg)](https://github.com/rogerhurwitz/yahtze/actions) -->

A Python library that implements Yahtzee game logic, scoring, and gameplay mechanics.

## Features

- Complete Yahtzee game engine with all official rules
- Dice rolling and re-rolling mechanics
- Automatic scoring calculation for all categories
- Game state management and turn tracking
- Support for multiple players
- AI player framework for automated gameplay
- Comprehensive validation and error handling

## Installation

### From PyPI
```bash
pip install yahtz
```

### From Source
```bash
git clone https://github.com/rogerhurwitz/yahtz.git
cd yahtz
pip install -e .
```

## Quick Start

```python
from yahtzee_engine import YahtzeeGame, Player

# Create a new game with players
game = YahtzeeGame()
game.add_player(Player("Alice"))
game.add_player(Player("Bob"))

# Start the game
game.start()

# Play a turn
current_player = game.current_player
dice_roll = current_player.roll_dice()
print(f"Rolled: {dice_roll}")

# Re-roll some dice (example: keep first two dice)
dice_roll = current_player.reroll([2, 3, 4])  # Re-roll dice at indices 2, 3, 4
print(f"After reroll: {dice_roll}")

# Score in a category
current_player.score_in_category("three_of_a_kind", dice_roll)

# End turn
game.next_turn()
```

## Core Components

### Game Classes
- `YahtzeeGame`: Main game controller
- `Player`: Individual player state and actions
- `ScoreCard`: Manages scoring categories and calculations
- `DiceRoll`: Represents a set of dice and rolling operations

### Scoring Categories
- Upper Section: Ones, Twos, Threes, Fours, Fives, Sixes
- Lower Section: Three of a Kind, Four of a Kind, Full House, Small Straight, Large Straight, Yahtzee, Chance
- Bonus calculations (Upper Section bonus, Yahtzee bonus)

### Game States
- Setup phase
- Active gameplay
- Turn management
- Game completion and winner determination

## API Reference

### YahtzeeGame

#### Methods
- `add_player(player)`: Add a player to the game
- `start()`: Initialize and start the game
- `next_turn()`: Advance to the next player's turn
- `is_game_over()`: Check if game has ended
- `get_winner()`: Get the winning player(s)
- `get_scores()`: Get current scores for all players

#### Properties
- `current_player`: Currently active player
- `turn_number`: Current turn number
- `players`: List of all players

### Player

#### Methods
- `roll_dice()`: Roll all five dice
- `reroll(indices)`: Re-roll specific dice by index
- `score_in_category(category, dice)`: Score dice in a category
- `get_available_categories()`: Get unscored categories
- `get_total_score()`: Calculate total score

#### Properties
- `name`: Player name
- `scorecard`: Player's scorecard
- `dice`: Current dice values
- `rolls_remaining`: Rolls left in current turn

### ScoreCard

#### Methods
- `score_category(category, dice)`: Calculate and record score
- `get_category_score(category)`: Get score for specific category
- `get_upper_total()`: Calculate upper section total
- `get_lower_total()`: Calculate lower section total
- `get_grand_total()`: Calculate final score
- `is_category_scored(category)`: Check if category is used

## Game Rules

### Basic Gameplay
The library implements standard Yahtzee rules:
- 13 rounds per game
- Up to 3 rolls per turn
- Players must score in exactly one category per turn
- Upper section bonus (35 points) for scoring 63+ points
- Yahtzee bonus (100 points) for additional Yahtzees

### Scoring Categories

#### Upper Section
- **Ones through Sixes**: Sum of matching dice
- **Bonus**: 35 points if upper section totals 63 or more

#### Lower Section
- **Three of a Kind**: Sum of all dice (if 3+ matching)
- **Four of a Kind**: Sum of all dice (if 4+ matching)  
- **Full House**: 25 points (3 of one kind + 2 of another)
- **Small Straight**: 30 points (4 consecutive numbers)
- **Large Straight**: 40 points (5 consecutive numbers)
- **Yahtzee**: 50 points (5 of a kind)
- **Chance**: Sum of all dice

## Examples

### Basic Game Loop
```python
from yahtzee_engine import YahtzeeGame, Player

def play_game():
    game = YahtzeeGame()
    game.add_player(Player("Player 1"))
    game.add_player(Player("Player 2"))
    game.start()
    
    while not game.is_game_over():
        player = game.current_player
        print(f"\n{player.name}'s turn")
        
        # Player's turn logic here
        # ... rolling, rerolling, scoring
        
        game.next_turn()
    
    winner = game.get_winner()
    print(f"Winner: {winner.name} with {winner.get_total_score()} points!")
```

### Custom Scoring Analysis
```python
from yahtzee_engine.analysis import ScoreAnalyzer

analyzer = ScoreAnalyzer()
probabilities = analyzer.calculate_category_probabilities([1, 1, 2, 3, 4])
best_category = analyzer.suggest_optimal_scoring([1, 1, 2, 3, 4])
```

### AI Player Implementation
```python
from yahtzee_engine.ai import BaseAIPlayer

class MyAIPlayer(BaseAIPlayer):
    def choose_dice_to_reroll(self, dice, available_categories):
        # Implement AI logic for dice selection
        return [0, 1]  # Reroll first two dice
    
    def choose_scoring_category(self, dice, available_categories):
        # Implement AI logic for category selection
        return "chance"  # Always choose chance
```

## Advanced Features

### Game Variants
- Forced Yahtzee rules
- Joker rules for filled categories
- Custom scoring modifications

### Statistics and Analysis
- Probability calculations for achieving categories
- Optimal strategy suggestions
- Game outcome analysis

### Extensibility
- Plugin system for custom rules
- Event hooks for game state changes
- Serialization support for game persistence

## Testing

Run the test suite:
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=yahtzee_engine --cov-report=html
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
git clone https://github.com/username/yahtzee-engine.git
cd yahtzee-engine
pip install -e ".[dev]"
pre-commit install
```

### Code Style
- Follow PEP 8
- Use type hints
- Maintain test coverage above 90%
- Document all public APIs

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## Support

- **Documentation**: [https://yahtzee-engine.readthedocs.io](https://yahtzee-engine.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/username/yahtzee-engine/issues)
- **Discussions**: [GitHub Discussions](https://github.com/username/yahtzee-engine/discussions)

## Acknowledgments

- Thanks to all contributors
- Inspired by the classic Yahtzee dice game
- Built with Python and love ❤️