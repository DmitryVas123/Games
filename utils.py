import os
import platform

def clear_terminal():
    """
    Clears the terminal screen in a cross-platform way.
    Works for Windows, macOS, and Linux.
    """
    try:
        # Detect the operating system
        current_os = platform.system()

        if current_os == "Windows":
            os.system("cls")  # Windows command
        else:
            os.system("clear")  # macOS/Linux command

    except Exception as e:
        print(f"Error clearing terminal: {e}")


def print_header(title):
    clear_terminal()
    print("=" * 40)
    print(title.center(40))
    print("=" * 40)
    print()

