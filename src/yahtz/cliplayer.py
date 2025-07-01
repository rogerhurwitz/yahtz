import sys
from typing import Any, Callable, Protocol


class MenuOption:
    """Represents a single menu option with its display text and action."""

    def __init__(self, text: str, action: Callable[[], Any], description: str = ""):
        self.text = text
        self.action = action
        self.description = description

    def execute(self):
        """Execute the option's action."""
        return self.action()


class Menu:
    """Represents a menu with options and display configuration."""

    def __init__(
        self,
        title: str,
        options: list[MenuOption] | None = None,
        show_numbers: bool = True,
    ):
        self.title = title
        self.options = options or []
        self.show_numbers = show_numbers

    def add_option(self, option: MenuOption) -> None:
        """Add an option to the menu."""
        self.options.append(option)

    def get_option(self, index: int) -> MenuOption | None:
        """Get option by index (0-based)."""
        if 0 <= index < len(self.options):
            return self.options[index]
        return None


# Protocol definitions for composition
class DisplayStrategy(Protocol):
    """Protocol for menu display strategies."""

    def display(self, menu: Menu) -> None:
        """Display the menu to the user."""


class InputStrategy(Protocol):
    """Protocol for menu input strategies."""

    def get_choice(self, menu: Menu) -> int | None:
        """Get user's menu choice. Returns 0-based index or None for invalid input."""


class ValidationStrategy(Protocol):
    """Protocol for input validation strategies."""

    def is_valid_choice(self, choice: str, menu: Menu) -> tuple[bool, int | None]:
        """Validate choice and return (is_valid, converted_index)."""
        return (False, None)


class ErrorHandlingStrategy(Protocol):
    """Protocol for error handling strategies."""

    def handle_invalid_input(self, choice: str, menu: Menu) -> None:
        """Handle invalid input from user."""


# Concrete implementations using composition
class SimpleDisplay:
    """Simple text-based menu display."""

    def __init__(
        self, separator: str = "-", width: int = 50, prefix_style: str = "numbered"
    ):
        self.separator = separator
        self.width = width
        self.prefix_style = prefix_style  # "numbered", "bullet", "none"

    def display(self, menu: Menu) -> None:
        """Display menu with title, separator, and options."""
        print(f"\n{menu.title}")
        print(self.separator * len(menu.title))

        for i, option in enumerate(menu.options, 1):
            prefix = self._get_prefix(i, menu.show_numbers)
            print(f"{prefix}{option.text}")
            if option.description:
                print(f"   {option.description}")
        print()

    def _get_prefix(self, index: int, show_numbers: bool) -> str:
        """Get the appropriate prefix for menu items."""
        if not show_numbers:
            return "• " if self.prefix_style == "bullet" else ""

        if self.prefix_style == "numbered":
            return f"{index}. "
        elif self.prefix_style == "bullet":
            return "• "
        else:
            return ""


class BoxedDisplay:
    """Boxed menu display with borders."""

    def __init__(self, box_char: str = "═", corner_char: str = "╔╗╚╝"):
        self.box_char = box_char
        self.corners = corner_char

    def display(self, menu: Menu) -> None:
        """Display menu in a box."""
        # Calculate box width
        max_width = max(
            len(menu.title),
            max(
                (len(f"{i}. {opt.text}") for i, opt in enumerate(menu.options, 1)),
                default=0,
            ),
        )
        box_width = max_width + 4

        # Top border
        print(f"\n{self.corners[0]}{self.box_char * (box_width - 2)}{self.corners[1]}")

        # Title
        title_padding = (box_width - 2 - len(menu.title)) // 2
        print(
            f"║{' ' * title_padding}{menu.title}{' ' * (box_width - 2 - title_padding - len(menu.title))}║"
        )
        print(f"║{self.box_char * (box_width - 2)}║")

        # Options
        for i, option in enumerate(menu.options, 1):
            option_text = f"{i}. {option.text}" if menu.show_numbers else option.text
            padding = box_width - 2 - len(option_text)
            print(f"║{option_text}{' ' * padding}║")

        # Bottom border
        print(f"{self.corners[2]}{self.box_char * (box_width - 2)}{self.corners[3]}\n")


class NumericValidation:
    """Validates numeric input for menu selection."""

    def is_valid_choice(self, choice: str, menu: Menu) -> tuple[bool, int | None]:
        """Validate numeric choice."""
        try:
            num_choice = int(choice.strip())
            if 1 <= num_choice <= len(menu.options):
                return True, num_choice - 1  # Convert to 0-based index
            return False, None
        except ValueError:
            return False, None


class LetterValidation:
    """Validates letter input for menu selection (a, b, c, etc.)."""

    def is_valid_choice(self, choice: str, menu: Menu) -> tuple[bool, int | None]:
        """Validate letter choice."""
        choice = choice.strip().lower()
        if len(choice) == 1 and choice.isalpha():
            index = ord(choice) - ord("a")
            if 0 <= index < len(menu.options):
                return True, index
        return False, None


class StandardInput:
    """Standard input handler that uses validation and error handling strategies."""

    def __init__(
        self,
        validator: ValidationStrategy | None = None,
        error_handler: ErrorHandlingStrategy | None = None,
        prompt: str = "Enter your choice: ",
    ):
        self.validator = validator or NumericValidation()
        self.error_handler = error_handler or StandardErrorHandler()
        self.prompt = prompt

    def get_choice(self, menu: Menu) -> int | None:
        """Get choice from user using composed validation."""
        try:
            choice = input(self.prompt)
            is_valid, index = self.validator.is_valid_choice(choice, menu)

            if is_valid:
                return index
            else:
                self.error_handler.handle_invalid_input(choice, menu)
                return None

        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)


class StandardErrorHandler:
    """Standard error handling for invalid menu input."""

    def __init__(self, message: str = "Invalid choice. Please try again."):
        self.message = message

    def handle_invalid_input(self, choice: str, menu: Menu) -> None:
        """Handle invalid input with standard message."""
        print(self.message)


class DetailedErrorHandler:
    """Detailed error handling that shows valid options."""

    def handle_invalid_input(self, choice: str, menu: Menu) -> None:
        """Handle invalid input with detailed feedback."""
        print(f"'{choice}' is not a valid option.")
        print(f"Please choose from 1-{len(menu.options)}")


class MenuSystem:
    """Main menu system using composition for all strategies."""

    def __init__(
        self,
        display_strategy: DisplayStrategy | None = None,
        input_strategy: InputStrategy | None = None,
    ):
        self.display = display_strategy or SimpleDisplay()
        self.input_handler = input_strategy or StandardInput()

    def run_menu(self, menu: Menu, loop: bool = True):
        """Run a menu, optionally in a loop until valid selection."""
        while True:
            self.display.display(menu)
            choice_index = self.input_handler.get_choice(menu)

            if choice_index is not None:
                option = menu.get_option(choice_index)
                if option:
                    result = option.execute()
                    if not loop:
                        return result
                    # If looping and action returns False, break the loop
                    if result is False:
                        break

            if not loop:
                break

    def run_menu_once(self, menu: Menu):
        """Run menu once without looping."""
        return self.run_menu(menu, loop=False)


class MenuBuilder:
    """Builder class to construct menus fluently."""

    def __init__(self, title: str):
        self.menu = Menu(title)

    def add_option(
        self, text: str, action: Callable[[], Any], description: str = ""
    ) -> "MenuBuilder":
        """Add an option to the menu being built."""
        self.menu.add_option(MenuOption(text, action, description))
        return self

    def add_separator(self, text: str = "---") -> "MenuBuilder":
        """Add a visual separator (non-selectable)."""
        self.menu.add_option(MenuOption(text, lambda: None))
        return self

    def add_exit_option(
        self, text: str = "Exit", action: Callable[[], Any] | None = None
    ) -> "MenuBuilder":
        """Add an exit option that returns False to break menu loops."""
        exit_action: Callable[[], Any] = action or (lambda: False)
        self.menu.add_option(MenuOption(text, exit_action))
        return self

    def set_numbering(self, show_numbers: bool) -> "MenuBuilder":
        """Set whether to show numbers for menu options."""
        self.menu.show_numbers = show_numbers
        return self

    def build(self) -> Menu:
        """Build and return the menu."""
        return self.menu


# Example usage and demonstration
def demo_basic_operations():
    """Demo function for basic operations."""
    print("Performing basic operation...")
    input("Press Enter to continue...")


def demo_advanced_operations():
    """Demo function for advanced operations."""
    print("Performing advanced operation...")
    name = input("Enter your name: ")
    print(f"Hello, {name}!")
    input("Press Enter to continue...")


def demo_settings():
    """Demo function showing different display and input styles."""
    print("Opening settings...")

    # Create a submenu with different styling
    settings_menu = (
        MenuBuilder("Settings")
        .add_option("Change Theme", lambda: print("Theme changed!"))
        .add_option("Update Profile", lambda: print("Profile updated!"))
        .add_separator()
        .add_exit_option("Back to Main Menu")
        .build()
    )

    # Use boxed display with letter input
    boxed_display = BoxedDisplay()
    letter_input = StandardInput(
        validator=LetterValidation(),
        error_handler=DetailedErrorHandler(),
        prompt="Enter your choice (a-d): ",
    )

    settings_system = MenuSystem(boxed_display, letter_input)
    settings_system.run_menu(settings_menu)


def demo_different_styles():
    """Demo showing different menu styles side by side."""
    demo_menu = (
        MenuBuilder("Style Demo")
        .add_option("Option 1", lambda: print("Selected 1"))
        .add_option("Option 2", lambda: print("Selected 2"))
        .add_exit_option()
        .build()
    )

    print("Standard Style:")
    standard_system = MenuSystem()
    standard_system.run_menu_once(demo_menu)

    print("\nBoxed Style with Letters:")
    boxed_system = MenuSystem(
        BoxedDisplay(), StandardInput(LetterValidation(), prompt="Choice (a-c): ")
    )
    boxed_system.run_menu_once(demo_menu)


def main():
    """Main function demonstrating the composed menu system."""

    # Create main menu
    main_menu = (
        MenuBuilder("Main Menu - Composition Demo")
        .add_option("Basic Operations", demo_basic_operations, "Perform basic tasks")
        .add_option(
            "Advanced Operations", demo_advanced_operations, "Perform advanced tasks"
        )
        .add_option(
            "Settings (Boxed + Letters)", demo_settings, "Configure with different UI"
        )
        .add_option(
            "Style Comparison", demo_different_styles, "Compare different menu styles"
        )
        .add_exit_option("Exit Application", lambda: (print("Goodbye!"), False)[1])
        .build()
    )

    # Create menu system with composed strategies
    display_strategy = SimpleDisplay(separator="=", prefix_style="numbered")
    input_strategy = StandardInput(
        validator=NumericValidation(),
        error_handler=DetailedErrorHandler(),
        prompt="Your choice: ",
    )

    menu_system = MenuSystem(display_strategy, input_strategy)

    # Run the main menu
    print("Welcome to the Composition-Based Menu System Demo!")
    menu_system.run_menu(main_menu)


if __name__ == "__main__":
    main()

# class CategoryChooser:
#     def __init__(self):
#         self.category: Box | None = None

#         states = ["main", "roll", "review", "select", "exit"]
#         transitions: list[dict[str, str | list[str]]] = [
#             {"trigger": "choose_roll", "source": "main", "dest": "roll"},
#             {"trigger": "choose_review", "source": "main", "dest": "review"},
#             {"trigger": "choose_select", "source": "main", "dest": "select"},
#             {
#                 "trigger": "back_to_main",
#                 "source": ["roll", "review", "select"],
#                 "dest": "main",
#             },
#             {"trigger": "choose_exit", "source": "main", "dest": "exit"},
#         ]

#         self.machine = Machine(
#             model=self, states=states, transitions=transitions, initial="main"
#         )

#     # Type hints for dynamically added methods and attributes by transitions
#     if TYPE_CHECKING:
#         # Dynamically added attributes by transitions
#         state: str

#         # Dynamically added methods by transitions
#         def choose_roll(self) -> None: ...
#         def choose_review(self) -> None: ...
#         def choose_select(self) -> None: ...
#         def choose_exit(self) -> None: ...
#         def back_to_main(self) -> None: ...

#     def run(self):
#         while self.state != "exit":
#             match self.state:
#                 case "main":
#                     self.do_main()
#                 case "roll":
#                     self.do_roll()
#                     self.back_to_main()
#                 case "review":
#                     self.do_review()
#                     self.back_to_main()
#                 case "select":
#                     self.do_select()
#                     self.back_to_main()
#                 case _:
#                     # This should never happen with the defined states
#                     pass

#     def do_main(self):
#         self.run_menu(
#             context="It's your turn. Choose an action:",
#             options=[
#                 "Review Scorecard",
#                 "Roll Dice",
#                 "Select Category",
#                 "Exit Game",
#             ],
#             handlers=[
#                 self.choose_review,
#                 self.choose_roll,
#                 self.choose_select,
#                 self.choose_exit,
#             ],
#         )

#     def do_roll(self):
#         print("Performing Roll")

#     def do_review(self):
#         print("Reviewing Scorecard")

#     def do_select(self):
#         print("Selecting Category")

#     def run_menu(
#         self,
#         context: str,
#         options: list[str],
#         handlers: list[Callable[[], None]],
#     ) -> None:
#         while True:
#             print(f"\n{context}")
#             for idx, option in enumerate(options, 1):
#                 print(f"{idx}. {option}")
#             print()
#             try:
#                 choice = int(input("Select an option: "))
#                 handlers[choice - 1]()
#                 break
#             except (ValueError, IndexError):
#                 print("** Invalid choice. Try again. **\n")
