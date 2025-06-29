#!/usr/bin/env python3
"""ZSH and shell-related utility functions for Mac setup scripts."""

import os
from pathlib import Path
from typing import List, Optional

from utils_core import (
    Colors,
    append_shell_section,
    command_exists,
    is_step_completed,
    mark_step_completed,
    print_error,
    print_info,
    print_success,
    print_warning,
    run_command,
)
from utils_install import install_brew_package


def setup_oh_my_zsh() -> None:
    """Install Oh My Zsh if not already installed."""
    if Path(f"{os.environ['HOME']}/.oh-my-zsh").exists():
        print_success("Oh My Zsh is already installed")
        return

    print_info("Installing Oh My Zsh...")
    run_command(
        'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"'
    )
    print_success("Oh My Zsh installed successfully")


def setup_zsh_autosuggestions() -> None:
    """Install and configure zsh-autosuggestions."""
    print_info("Setting up zsh-autosuggestions...")

    # Install zsh-autosuggestions
    install_brew_package("zsh-autosuggestions", "formula")

    # Add to .zshrc
    append_shell_section(
        "zsh-autosuggestions",
        ["source $(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh"],
    )

    print_success(
        "zsh-autosuggestions configured. Start a new terminal session to activate."
    )


def setup_fzf() -> None:
    """Install and configure fzf with shell integration."""
    print_info("Setting up fzf...")

    install_brew_package("fd", "formula")
    install_brew_package("bat", "formula")

    # Install fzf
    install_brew_package("fzf", "formula")

    # Add shell integration to .zshrc
    append_shell_section("fzf shell integration", ["source <(fzf --zsh)"])

    print_success(
        "fzf configured with shell integration. Start a new terminal session to activate."
    )


def setup_authjump() -> None:
    """Install and configure authjump for SSH management."""
    print_info("Setting up authjump...")

    # Install authjump via Homebrew
    install_brew_package("authjump", "formula")

    # Add to .zshrc
    append_shell_section(
        "authjump",
        [
            'export AUTHJUMP_CONFIG="$HOME/.authjump/config"',
            'export AUTHJUMP_CACHE_DIR="$HOME/.authjump/cache"',
            "source $(brew --prefix)/opt/authjump/share/authjump/authjump.zsh",
        ],
    )

    print_success("authjump configured. Start a new terminal session to activate.")


def setup_fast_syntax_highlighting() -> None:
    """Install fast-syntax-highlighting for Oh-My-Zsh."""
    print_info("Setting up fast-syntax-highlighting...")

    # Check if already cloned
    check_cmd = '[ -d "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/fast-syntax-highlighting" ]'
    if run_command(check_cmd, check=False) is not None:
        print_success("fast-syntax-highlighting is already installed")
        return

    # Clone to ZSH_CUSTOM directory
    clone_cmd = "git clone https://github.com/zdharma-continuum/fast-syntax-highlighting.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/fast-syntax-highlighting"
    run_command(clone_cmd)
    print_success("fast-syntax-highlighting installed successfully")


def setup_atuin() -> None:
    """Install and configure Atuin for shell history sync."""
    print_info("Setting up Atuin...")

    # Check if already installed
    if command_exists("atuin"):
        print_success("Atuin is already installed")
    else:
        # Install Atuin
        print_info("Installing Atuin...")
        run_command("curl --proto '=https' --tlsv1.2 -LsSf https://setup.atuin.sh | sh")

        # Import existing shell history
        print_info("Importing shell history...")
        run_command("atuin import auto")

    # Add Atuin to shell config
    append_shell_section(
        "Atuin shell history",
        [
            'export PATH="$HOME/.atuin/bin:$PATH"',
            'eval "$(atuin init zsh --disable-up-arrow)"',
        ],
    )

    print_success("Atuin configured successfully")
    print_info("Your shell history is now searchable with Ctrl+R")

    # Check if user needs to login
    flag_name = "atuin_login_completed"
    if not is_step_completed(flag_name):
        print("\n" + "=" * 60)
        print(f"{Colors.YELLOW}⚠️  MANUAL CONFIGURATION REQUIRED ⚠️{Colors.RESET}")
        print("=" * 60)
        print(f"\n{Colors.BLUE}To enable Atuin sync across devices:{Colors.RESET}")
        print("  1. Open a new terminal")
        print("  2. Run: atuin register -u <USERNAME> -e <EMAIL>")
        print("  3. Or login with: atuin login -u <USERNAME>")
        print("  4. This enables history sync across all your devices")
        print("\n  Note: This step is optional. Atuin works locally without login.")
        print("=" * 60 + "\n")

        response = input(
            f"{Colors.YELLOW}Type 'done' when you have completed this step (or 'skip' to continue without sync): {Colors.RESET}"
        )
        while response.lower() not in ["done", "skip"]:
            response = input(
                f"{Colors.YELLOW}Please type 'done' or 'skip' to continue: {Colors.RESET}"
            )

        if response.lower() == "done":
            run_command("atuin sync")
            mark_step_completed(flag_name)
            print_success("Atuin login configuration completed")
        else:
            print_info(
                "Skipping Atuin sync setup - you can set it up later with 'atuin login'"
            )


def setup_custom_aliases() -> None:
    """Setup custom shell aliases."""
    print_info("Setting up custom aliases...")

    aliases = [
        'CODE_EDITOR="code"',
        "",
        'alias p="pnpm"',
        'alias gp="git push"',
        'alias code_editor="$CODE_EDITOR"',
        'alias pt="pet exec"',
        'alias rc=\'RC_FILE="$HOME/.zshrc"',
        '${CODE_EDITOR} "$RC_FILE" -w',
        'source "$RC_FILE"',
        'echo "sourced $RC_FILE"',
        "'",
    ]

    append_shell_section("Custom aliases", aliases)
    print_success("Custom aliases configured")


def align_zsh_plugins(
    desired_plugins: List[str], zshrc_path: Optional[str] = None
) -> None:
    """Align zsh plugins with a provided list.

    This function updates the plugins array in .zshrc to match the desired plugins list.
    Handles both single-line and multi-line plugin declarations.

    Args:
        desired_plugins: List of plugin names to set in .zshrc
        zshrc_path: Optional path to .zshrc file (defaults to ~/.zshrc)

    Example:
        align_zsh_plugins(['git', 'docker', 'npm', 'zsh-autosuggestions'])
    """
    config_path = Path(zshrc_path or f"{os.environ['HOME']}/.zshrc")

    if not config_path.exists():
        print_error(f".zshrc file not found at {config_path}")
        return

    # Read current content
    lines = config_path.read_text().splitlines()

    # Find plugins declaration start
    plugin_start = -1
    plugin_end = -1

    for i, line in enumerate(lines):
        if line.strip().startswith("plugins="):
            plugin_start = i
            # Check if it's a single line (contains closing parenthesis)
            if ")" in line:
                plugin_end = i
            else:
                # Multi-line: find the closing parenthesis
                for j in range(i + 1, len(lines)):
                    if ")" in lines[j]:
                        plugin_end = j
                        break
            break

    if plugin_start >= 0 and plugin_end >= 0:
        # Delete old lines (from start to end inclusive)
        for _ in range(plugin_end - plugin_start + 1):
            lines.pop(plugin_start)

        # Insert new single-line plugins declaration
        lines.insert(plugin_start, f"plugins=({' '.join(desired_plugins)})")

        # Write back
        config_path.write_text("\n".join(lines) + "\n")
        print_success(
            f"Updated plugins in {config_path}: ({' '.join(desired_plugins)})"
        )
    else:
        print_error("No complete plugins declaration found in .zshrc")


def setup_iterm2_natural_text_editing() -> None:
    """Configure iTerm2 for natural text editing (word jumps and deletions)."""
    flag_name = "setup_iterm2_natural_text_editing"

    # Check if already completed
    if is_step_completed(flag_name):
        print_success("iTerm2 natural text editing already configured")
        return

    print_info("Configuring iTerm2 for natural text editing...")

    # Check if iTerm2 is installed
    iterm_path = Path("/Applications/iTerm.app")
    if not iterm_path.exists():
        print_warning(
            "iTerm2 is not installed. Skipping natural text editing configuration."
        )
        return

    print("\n" + "=" * 60)
    print(f"{Colors.YELLOW}⚠️  MANUAL CONFIGURATION REQUIRED ⚠️{Colors.RESET}")
    print("=" * 60)
    print(f"\n{Colors.BLUE}To enable natural text editing in iTerm2:{Colors.RESET}")
    print("  1. Open iTerm2")
    print("  2. Go to iTerm → Preferences → Profiles → Keys → Key mappings")
    print("  3. Click Presets... → Natural Text Editing")
    print("  4. This enables word jumps (⌥ + ←/→) and word deletion (⌥ + backspace)")
    print("=" * 60 + "\n")

    response = input(
        f"{Colors.YELLOW}Type 'done' when you have completed this step: {Colors.RESET}"
    )
    while response.lower() != "done":
        response = input(
            f"{Colors.YELLOW}Please type 'done' to continue: {Colors.RESET}"
        )

    mark_step_completed(flag_name)
    print_success("iTerm2 natural text editing configuration completed")
