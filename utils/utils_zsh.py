#!/usr/bin/env python3
"""ZSH and shell-related utility functions for Mac setup scripts.

This module provides functions to set up and configure various ZSH-related tools
and enhancements including Oh My Zsh, shell plugins, and productivity tools.
"""

import os
from pathlib import Path
from typing import List, Optional

from .utils_core import (
    Colors,
    append_shell_section,
    command_exists,
    is_step_completed,
    mark_step_completed,
    print_error,
    print_info,
    print_success,
    print_warning,
    prompt_for_user_input,
    run_command,
)
from .utils_install import install_brew_package

# Constants
OH_MY_ZSH_INSTALL_URL = "https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh"
FAST_SYNTAX_HIGHLIGHTING_REPO = "https://github.com/zdharma-continuum/fast-syntax-highlighting.git"
ATUIN_INSTALL_URL = "https://setup.atuin.sh"
MANUAL_CONFIG_SEPARATOR = "=" * 60


def setup_oh_my_zsh() -> None:
    """Install Oh My Zsh framework if not already installed.

    Oh My Zsh is a framework for managing ZSH configuration with themes
    and plugins support.
    """
    oh_my_zsh_dir = Path(os.environ["HOME"]) / ".oh-my-zsh"

    if oh_my_zsh_dir.exists():
        print_success("Oh My Zsh is already installed")
        return

    print_info("Installing Oh My Zsh...")
    install_command = f'sh -c "$(curl -fsSL {OH_MY_ZSH_INSTALL_URL})"'
    run_command(install_command)
    print_success("Oh My Zsh installed successfully")


def setup_zsh_autosuggestions() -> None:
    """Install and configure zsh-autosuggestions plugin.

    This plugin suggests commands as you type based on history and completions.
    """
    print_info("Setting up zsh-autosuggestions...")

    # Install the plugin via Homebrew
    install_brew_package("zsh-autosuggestions", "formula")

    # Configure shell integration
    autosuggestions_source = "source $(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh"
    append_shell_section("zsh-autosuggestions", [autosuggestions_source])

    print_success("zsh-autosuggestions configured. Start a new terminal session to activate.")


def setup_fzf() -> None:
    """Install and configure fzf (fuzzy finder) with shell integration.

    Also installs fd (better find) and bat (better cat) for enhanced functionality.
    """
    print_info("Setting up fzf...")

    # Install dependencies for better fzf experience
    install_brew_package("fd", "formula")  # Fast file finder
    install_brew_package("bat", "formula")  # Syntax highlighting for file preview

    # Install fzf itself
    install_brew_package("fzf", "formula")

    # Add shell integration to enable keybindings
    append_shell_section("fzf shell integration", ["source <(fzf --zsh)"])

    print_success("fzf configured with shell integration. Start a new terminal session to activate.")


def setup_autojump() -> None:
    """Install and configure authjump for intelligent directory navigation.

    Authjump learns your most used directories and allows quick navigation
    using the 'j' command.
    """
    print_info("Setting up authjump...")

    # Install via Homebrew
    install_brew_package("authjump", "formula")

    # Configure environment variables and source the script
    authjump_config = [
        'export AUTHJUMP_CONFIG="$HOME/.authjump/config"',
        'export AUTHJUMP_CACHE_DIR="$HOME/.authjump/cache"',
        "source $(brew --prefix)/opt/authjump/share/authjump/authjump.zsh",
    ]

    append_shell_section("authjump", authjump_config)
    print_success("authjump configured. Start a new terminal session to activate.")


def setup_fast_syntax_highlighting() -> None:
    """Install fast-syntax-highlighting plugin for Oh-My-Zsh.

    Provides real-time syntax highlighting for commands as you type them.
    """
    print_info("Setting up fast-syntax-highlighting...")

    # Determine the custom plugins directory
    zsh_custom = os.environ.get("ZSH_CUSTOM", f"{os.environ['HOME']}/.oh-my-zsh/custom")
    plugin_dir = Path(zsh_custom) / "plugins" / "fast-syntax-highlighting"

    # Check if plugin is already installed
    if plugin_dir.exists():
        print_success("fast-syntax-highlighting is already installed")
        return

    # Clone the plugin repository
    clone_command = (
        f"git clone {FAST_SYNTAX_HIGHLIGHTING_REPO} "
        f"${{ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}}/plugins/fast-syntax-highlighting"
    )
    run_command(clone_command)
    print_success("fast-syntax-highlighting installed successfully")


def _print_manual_config_header(title: str) -> None:
    """Print a formatted header for manual configuration sections.

    Args:
        title: The title to display in the header
    """
    print(f"\n{MANUAL_CONFIG_SEPARATOR}")
    print(f"{Colors.YELLOW}⚠️  {title} ⚠️{Colors.RESET}")
    print(MANUAL_CONFIG_SEPARATOR)


def setup_atuin() -> None:
    """Install and configure Atuin for advanced shell history management.

    Atuin provides searchable, syncable shell history with powerful features
    like context search, directory filtering, and cross-device sync.
    """
    print_info("Setting up Atuin...")

    # Check if Atuin is already installed
    if command_exists("atuin"):
        print_success("Atuin is already installed")
    else:
        # Install Atuin using their official installer
        print_info("Installing Atuin...")
        install_command = f"curl --proto '=https' --tlsv1.2 -LsSf {ATUIN_INSTALL_URL} | sh"
        run_command(install_command)

        # Import existing shell history into Atuin
        print_info("Importing shell history...")
        run_command("atuin import auto")

    # Configure shell integration
    atuin_config = [
        'export PATH="$HOME/.atuin/bin:$PATH"',
        'eval "$(atuin init zsh --disable-up-arrow)"',  # Keep up-arrow for normal history
    ]
    append_shell_section("Atuin shell history", atuin_config)

    print_success("Atuin configured successfully")
    print_info("Your shell history is now searchable with Ctrl+R")

    # Handle optional sync setup
    _handle_atuin_sync_setup()


def _handle_atuin_sync_setup() -> None:
    """Handle the optional Atuin sync configuration.

    This is a separate function to keep the main setup function cleaner.
    """
    flag_name = "atuin_login_completed"

    if is_step_completed(flag_name):
        return

    _print_manual_config_header("MANUAL CONFIGURATION REQUIRED")

    print(f"\n{Colors.BLUE}To enable Atuin sync across devices:{Colors.RESET}")
    print("  1. Open a new terminal")
    print("  2. Run: atuin register -u <USERNAME> -e <EMAIL>")
    print("  3. Or login with: atuin login -u <USERNAME>")
    print("  4. This enables history sync across all your devices")
    print("\n  Note: This step is optional. Atuin works locally without login.")
    print(f"{MANUAL_CONFIG_SEPARATOR}\n")

    response = prompt_for_user_input(
        "Type 'done' when you have completed this step (or 'skip' to continue without sync)",
        valid_responses=["done", "skip"],
    )

    if response == "done":
        run_command("atuin sync")
        mark_step_completed(flag_name)
        print_success("Atuin login configuration completed")
    else:
        print_info("Skipping Atuin sync setup - you can set it up later with 'atuin login'")


def setup_custom_aliases() -> None:
    """Configure custom shell aliases for improved productivity.

    Sets up commonly used shortcuts and convenience commands.
    """
    print_info("Setting up custom aliases...")

    # Define aliases with clear organization
    aliases = [
        # Editor configuration
        'CODE_EDITOR="code"',
        "",
        # Package manager shortcuts
        'alias p="pnpm"',
        # Git shortcuts
        'alias gp="git push"',
        # Editor alias
        'alias code_editor="$CODE_EDITOR"',
        # Pet (command snippet manager) shortcut
        'alias pt="pet exec"',
        # Quick .zshrc reload command
        'alias rc=\'RC_FILE="$HOME/.zshrc"',
        '${CODE_EDITOR} "$RC_FILE" -w',
        'source "$RC_FILE"',
        'echo "sourced $RC_FILE"',
        "'",
    ]

    append_shell_section("Custom aliases", aliases)
    print_success("Custom aliases configured")


def align_zsh_plugins(desired_plugins: List[str], zshrc_path: Optional[str] = None) -> None:
    """Update the Oh My Zsh plugins list in .zshrc to match desired plugins.

    This function finds and replaces the plugins array in .zshrc, handling
    both single-line and multi-line plugin declarations.

    Args:
        desired_plugins: List of plugin names to set in .zshrc
        zshrc_path: Optional path to .zshrc file (defaults to ~/.zshrc)

    Example:
        >>> align_zsh_plugins(['git', 'docker', 'npm', 'zsh-autosuggestions'])

    Note:
        This function modifies the .zshrc file in place. Make sure to have
        a backup before running.
    """
    config_path = Path(zshrc_path or f"{os.environ['HOME']}/.zshrc")

    if not config_path.exists():
        print_error(f".zshrc file not found at {config_path}")
        return

    # Read current configuration
    lines = config_path.read_text().splitlines()

    # Find the plugins declaration
    plugin_indices = _find_plugin_declaration(lines)

    if plugin_indices is None:
        print_error("No complete plugins declaration found in .zshrc")
        return

    start_index, end_index = plugin_indices

    # Replace the old plugin declaration with new one
    _replace_plugin_declaration(lines, start_index, end_index, desired_plugins)

    # Write the updated configuration
    config_path.write_text("\n".join(lines) + "\n")
    print_success(f"Updated plugins in {config_path}: ({' '.join(desired_plugins)})")


def _find_plugin_declaration(lines: List[str]) -> Optional[tuple[int, int]]:
    """Find the start and end indices of the plugins declaration.

    Args:
        lines: List of lines from .zshrc

    Returns:
        Tuple of (start_index, end_index) or None if not found
    """
    for i, line in enumerate(lines):
        if line.strip().startswith("plugins="):
            start_index = i

            # Check if it's a single-line declaration
            if ")" in line:
                return (start_index, i)

            # Multi-line declaration: find the closing parenthesis
            for j in range(i + 1, len(lines)):
                if ")" in lines[j]:
                    return (start_index, j)

            # No closing parenthesis found
            break

    return None


def _replace_plugin_declaration(lines: List[str], start_index: int, end_index: int, desired_plugins: List[str]) -> None:
    """Replace the plugin declaration in the lines list.

    Args:
        lines: List of lines to modify (modified in place)
        start_index: Index of the first line of plugin declaration
        end_index: Index of the last line of plugin declaration
        desired_plugins: List of plugins to set
    """
    # Remove old declaration lines
    for _ in range(end_index - start_index + 1):
        lines.pop(start_index)

    # Insert new single-line plugins declaration
    plugins_line = f"plugins=({' '.join(desired_plugins)})"
    lines.insert(start_index, plugins_line)


def setup_iterm2_natural_text_editing() -> None:
    """Configure iTerm2 for natural text editing keybindings.

    Enables word jumps (Option + Arrow) and word deletion (Option + Delete)
    for a more natural text editing experience in the terminal.
    """
    flag_name = "setup_iterm2_natural_text_editing"

    # Skip if already configured
    if is_step_completed(flag_name):
        print_success("iTerm2 natural text editing already configured")
        return

    print_info("Configuring iTerm2 for natural text editing...")

    # Check if iTerm2 is installed
    iterm_app_path = Path("/Applications/iTerm.app")
    if not iterm_app_path.exists():
        print_warning("iTerm2 is not installed. Skipping natural text editing configuration.")
        return

    # Guide user through manual configuration
    _print_manual_config_header("MANUAL CONFIGURATION REQUIRED")

    print(f"\n{Colors.BLUE}To enable natural text editing in iTerm2:{Colors.RESET}")
    print("  1. Open iTerm2")
    print("  2. Go to iTerm → Preferences → Profiles → Keys → Key mappings")
    print("  3. Click Presets... → Natural Text Editing")
    print("  4. This enables word jumps (⌥ + ←/→) and word deletion (⌥ + backspace)")
    print(f"{MANUAL_CONFIG_SEPARATOR}\n")

    response = prompt_for_user_input("Type 'done' when you have completed this step", expected_response="done")

    mark_step_completed(flag_name)
    print_success("iTerm2 natural text editing configuration completed")


def setup_mitm_chrome() -> None:
    """Configure a zsh function for Chrome incognito with mitmproxy.

    This sets up a `chrome` function in zshrc that:
      - Launches Chrome with an isolated temporary profile in incognito
      - Routes traffic through a mitmproxy listening on localhost:8080
      - Cleans up the temporary profile directory when Chrome exits or you press Ctrl+C
    """
    print_info("Setting up chrome helper...")

    mitm_chrome_func = [
        "chrome() { TMP_DIR=\"$(mktemp -d)\" && CHROME=\"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome\" && \"$CHROME\" --user-data-dir=\"$TMP_DIR\" --incognito --disable-extensions --no-default-browser-check --no-first-run --disable-features=MetricsReporting --proxy-server=\"http://127.0.0.1:8080\" --proxy-bypass-list=\"\" & PID=$! && trap \"kill -9 $PID 2>/dev/null; rm -rf \\\"$TMP_DIR\\\"\" INT TERM EXIT && wait $PID; }",
    ]

    append_shell_section("chrome helper", mitm_chrome_func)
    print_success("Chrome helper configured. Open a new shell and run `chrome`.")
