"""Entry point for the poker CLI game."""

import sys


def main() -> None:
    # Quick sanity check for Python version
    if sys.version_info < (3, 11):
        print("Python 3.11+ required.")
        sys.exit(1)

    try:
        from .game import PokerSession
        session = PokerSession()
        session.main_menu()
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
