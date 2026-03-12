"""Terminal display helpers."""

import os
import shutil

# ANSI colors
BOLD    = "\033[1m"
DIM     = "\033[2m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
MAGENTA = "\033[95m"
RED     = "\033[91m"
BLUE    = "\033[94m"
WHITE   = "\033[97m"
RESET   = "\033[0m"

TITLE = rf"""
{YELLOW}{BOLD}
 ██████╗  ██████╗ ██╗  ██╗███████╗██████╗
 ██╔══██╗██╔═══██╗██║ ██╔╝██╔════╝██╔══██╗
 ██████╔╝██║   ██║█████╔╝ █████╗  ██████╔╝
 ██╔═══╝ ██║   ██║██╔═██╗ ██╔══╝  ██╔══██╗
 ██║     ╚██████╔╝██║  ██╗███████╗██║  ██║
 ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
{RESET}{DIM}       Texas Hold'em — Command Line Edition{RESET}
"""


def term_width() -> int:
    return shutil.get_terminal_size((80, 24)).columns


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def separator(char: str = "─", color: str = DIM) -> str:
    return f"{color}{char * term_width()}{RESET}"


def header(text: str, color: str = CYAN) -> str:
    w = term_width()
    padded = f"  {text}  "
    side = (w - len(padded)) // 2
    return f"{color}{BOLD}{'─' * side}{padded}{'─' * side}{RESET}"


def fmt_money(amount: int) -> str:
    return f"{GREEN}${amount:,}{RESET}"


def fmt_pot(amount: int) -> str:
    return f"{YELLOW}${amount:,}{RESET}"


def fmt_name(name: str, is_human: bool = False, folded: bool = False, all_in: bool = False) -> str:
    if folded:
        return f"{DIM}{name} [folded]{RESET}"
    if all_in:
        return f"{RED}{BOLD}{name} [ALL IN]{RESET}"
    if is_human:
        return f"{CYAN}{BOLD}{name}{RESET}"
    return f"{MAGENTA}{name}{RESET}"


def print_title() -> None:
    print(TITLE)


def menu(options: list[tuple[str, str]]) -> None:
    """Print a numbered menu. options = [(key, label), ...]"""
    print()
    for key, label in options:
        print(f"  {YELLOW}{BOLD}[{key}]{RESET}  {label}")
    print()


def prompt(text: str) -> str:
    return input(f"{CYAN}{BOLD}▶ {text}: {RESET}").strip()


def info(text: str) -> None:
    print(f"  {WHITE}{text}{RESET}")


def success(text: str) -> None:
    print(f"  {GREEN}✔ {text}{RESET}")


def warn(text: str) -> None:
    print(f"  {YELLOW}⚠ {text}{RESET}")


def error(text: str) -> None:
    print(f"  {RED}✖ {text}{RESET}")


def action_log(text: str) -> None:
    print(f"  {DIM}» {text}{RESET}")


def press_enter() -> None:
    input(f"\n  {DIM}Press Enter to continue...{RESET}")
