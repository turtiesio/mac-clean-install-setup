#!/usr/bin/env python3
"""Application-specific utility functions for Mac setup scripts.

This module contains functions for setting up various applications and tools
on macOS, including Git configuration, h-cli installation, and keyboard
remapping utilities.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Tuple

from .utils_core import (
    Colors,
    create_launch_agent,
    is_step_completed,
    mark_step_completed,
    print_info,
    print_success,
    print_warning,
    prompt_for_user_input,
    run_command,
)

# Constants for better maintainability
H_CLI_REPO_URL = "https://github.com/turtiesio/h-cli.git"
H_CLI_DIR_NAME = ".h-cli"
H_CLI_CONFIG_DIR_NAME = ".config/h-cli"
H_CLI_CONFIG_FILE_NAME = "config.yaml"

# Korean-English key remapping constants
KEY_REMAPPING_LABEL = "com.example.KeyRemapping"
KEY_REMAPPING_SRC = 0x700000039  # Caps Lock key
KEY_REMAPPING_DST = 0x70000006D  # F18 key


def setup_korean_english_key_remapping() -> None:
    """Set up Korean-English switching delay configuration.

    This function remaps the Caps Lock key to F18 to improve the Korean-English
    input switching experience on macOS. It creates a persistent launch agent
    to maintain the setting across system restarts.
    """
    print_info("한영 전환 딜레이 설정")

    # Build the key mapping configuration
    key_mapping_json = (
        f'{{"UserKeyMapping":[{{"HIDKeyboardModifierMappingSrc": '
        f'{KEY_REMAPPING_SRC:#x}, "HIDKeyboardModifierMappingDst": '
        f"{KEY_REMAPPING_DST:#x}}}]}}"
    )

    # Apply the key remapping immediately
    run_command(f"hidutil property --set '{key_mapping_json}'")

    # Create launch agent XML with proper formatting
    launch_agent_xml = _create_key_remapping_plist(key_mapping_json)

    # Create persistent launch agent
    create_launch_agent(KEY_REMAPPING_LABEL, launch_agent_xml)


def _create_key_remapping_plist(key_mapping_json: str) -> str:
    """Create a properly formatted plist XML for key remapping launch agent.

    Args:
        key_mapping_json: The JSON string containing key mapping configuration

    Returns:
        str: Formatted plist XML content
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{KEY_REMAPPING_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/hidutil</string>
        <string>property</string>
        <string>--set</string>
        <string>{key_mapping_json}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""


def setup_h_cli() -> None:
    """Install and configure h-cli from GitHub repository.

    This function handles the complete setup of h-cli including:
    - Cloning or updating the repository
    - Installing the CLI globally
    - Setting up default configuration
    - Prompting for API key configuration
    """
    print_info("Setting up h-cli...")

    # Define paths
    home_dir = Path(os.environ["HOME"])
    h_cli_dir = home_dir / H_CLI_DIR_NAME

    # Install or update h-cli
    if h_cli_dir.exists():
        _update_h_cli_if_needed(h_cli_dir)
    else:
        _install_h_cli(h_cli_dir)

    # Set up configuration
    _setup_h_cli_config(home_dir, h_cli_dir)

    print_info("You can now use 'h' command. Try 'h --help' to see available commands.")


def _update_h_cli_if_needed(h_cli_dir: Path) -> None:
    """Check for h-cli updates and install if available.

    Args:
        h_cli_dir: Path to the h-cli directory
    """
    # Fetch latest changes
    run_command(f"cd {h_cli_dir} && git fetch", check=False)

    # Determine default branch
    default_branch = _get_default_branch(h_cli_dir)

    # Compare local and remote commits
    local_hash, remote_hash = _get_git_hashes(h_cli_dir, default_branch)

    if local_hash and remote_hash and local_hash != remote_hash:
        print_info("Updates available for h-cli...")
        run_command(f"cd {h_cli_dir} && git pull")
        _install_h_cli_globally(h_cli_dir)
    else:
        print_success("h-cli is already up to date")


def _get_default_branch(h_cli_dir: Path) -> str:
    """Determine the default branch name for the Git repository.

    Args:
        h_cli_dir: Path to the Git repository

    Returns:
        str: The default branch name ('main' or 'master')
    """
    # Try to get default branch from symbolic ref
    default_branch = run_command(
        f"cd {h_cli_dir} && git symbolic-ref refs/remotes/origin/HEAD | "
        f"sed 's@^refs/remotes/origin/@@'",
        check=False,
    )

    if default_branch:
        return default_branch

    # Fallback: check if master branch exists
    has_master = run_command(
        f"cd {h_cli_dir} && git branch -r | grep -q origin/master", check=False
    )

    return "master" if has_master is not None else "main"


def _get_git_hashes(
    h_cli_dir: Path, branch: str
) -> Tuple[Optional[str], Optional[str]]:
    """Get local and remote Git commit hashes.

    Args:
        h_cli_dir: Path to the Git repository
        branch: Name of the branch to check

    Returns:
        Tuple of (local_hash, remote_hash)
    """
    local_hash = run_command(f"cd {h_cli_dir} && git rev-parse HEAD", check=False)
    remote_hash = run_command(
        f"cd {h_cli_dir} && git rev-parse origin/{branch}", check=False
    )

    return local_hash, remote_hash


def _install_h_cli(h_cli_dir: Path) -> None:
    """Clone h-cli repository and install it globally.

    Args:
        h_cli_dir: Path where h-cli should be installed
    """
    print_info("Cloning h-cli repository...")
    run_command(f"git clone {H_CLI_REPO_URL} {h_cli_dir}")
    _install_h_cli_globally(h_cli_dir)


def _install_h_cli_globally(h_cli_dir: Path) -> None:
    """Install h-cli globally using make.

    Args:
        h_cli_dir: Path to the h-cli directory
    """
    print_info("Installing h-cli globally...")
    run_command(f"cd {h_cli_dir} && make install-global")
    print_success("h-cli installed successfully")


def _setup_h_cli_config(home_dir: Path, h_cli_dir: Path) -> None:
    """Set up h-cli configuration and prompt for API keys.

    Args:
        home_dir: User's home directory path
        h_cli_dir: Path to the h-cli installation
    """
    # Define configuration paths
    config_dir = home_dir / H_CLI_CONFIG_DIR_NAME
    config_file = config_dir / H_CLI_CONFIG_FILE_NAME

    # Copy default config if needed
    if not config_file.exists():
        _copy_default_config(h_cli_dir, config_dir, config_file)

    # Prompt for API keys
    _prompt_for_api_keys(config_file)


def _copy_default_config(h_cli_dir: Path, config_dir: Path, config_file: Path) -> None:
    """Copy default configuration from h-cli repository.

    Args:
        h_cli_dir: Path to the h-cli installation
        config_dir: Path to the configuration directory
        config_file: Path to the configuration file
    """
    print_info("Setting up h-cli configuration...")
    config_dir.mkdir(parents=True, exist_ok=True)

    # Look for default config in the repository
    default_config = h_cli_dir / "config" / "default.yaml"

    if default_config.exists():
        shutil.copy2(default_config, config_file)
        print_success("Copied default h-cli config")
    else:
        print_warning("Could not find default config in h-cli repository")


def _prompt_for_api_keys(config_file: Path) -> None:
    """Prompt user to configure API keys for h-cli.

    Args:
        config_file: Path to the h-cli configuration file
    """
    flag_name = "h_cli_api_keys_configured"

    if is_step_completed(flag_name):
        return

    # Display configuration instructions
    _display_api_key_instructions(config_file)

    # Get user response
    response = prompt_for_user_input(
        "Type 'done' when you have added your API keys (or 'skip' to configure later)",
        valid_responses=["done", "skip"],
    )

    # Handle response
    if response == "done":
        mark_step_completed(flag_name)
        print_success("h-cli API keys configured")
    else:
        print_info(f"You can configure API keys later by editing: {config_file}")


def _display_api_key_instructions(config_file: Path) -> None:
    """Display instructions for configuring API keys.

    Args:
        config_file: Path to the configuration file
    """
    print("\n" + "=" * 60)
    print(f"{Colors.YELLOW}⚠️  MANUAL CONFIGURATION REQUIRED ⚠️{Colors.RESET}")
    print("=" * 60)
    print(f"\n{Colors.BLUE}Configure h-cli API keys:{Colors.RESET}")
    print(f"  1. Open config: {config_file}")
    print("  2. Add your API keys:")
    print("     • gemini_api_key: Get from https://makersuite.google.com/app/apikey")
    print("     • openrouter_api_key: Get from https://openrouter.ai/keys")
    print("\n  Note: h-cli will work without API keys but AI features will be limited.")
    print("=" * 60 + "\n")


def setup_git_config() -> None:
    """Set up Git global configuration with user name and email.

    This function checks for existing Git configuration and prompts the user
    to set up their name and email if not already configured. It also sets
    sensible defaults for branch naming and pull strategy.
    """
    print_info("Setting up Git configuration...")

    # Check existing configuration
    existing_name = run_command("git config --global user.name", check=False)
    existing_email = run_command("git config --global user.email", check=False)

    if existing_name and existing_email:
        _display_existing_git_config(existing_name, existing_email)
        return

    # Get new configuration from user
    name, email = _get_git_config_from_user()

    # Apply configuration
    _apply_git_config(name, email)


def _display_existing_git_config(name: str, email: str) -> None:
    """Display existing Git configuration.

    Args:
        name: Configured Git user name
        email: Configured Git user email
    """
    print_info("Git already configured:")
    print_info(f"  Name: {name}")
    print_info(f"  Email: {email}")
    print_success("Keeping existing Git configuration")


def _get_git_config_from_user() -> Tuple[str, str]:
    """Prompt user for Git configuration details.

    Returns:
        Tuple of (name, email) provided by the user
    """
    print(f"\n{Colors.BLUE}Configure Git global settings:{Colors.RESET}")

    # Get name with validation
    name = _prompt_for_name()

    # Get email with validation
    email = _prompt_for_email()

    return name, email


def _prompt_for_name() -> str:
    """Prompt user for their full name with validation.

    Returns:
        str: The user's full name
    """
    prompt = f"{Colors.BLUE}Enter your full name (for Git commits): {Colors.RESET}"
    name = input(prompt).strip()

    while not name:
        prompt = (
            f"{Colors.YELLOW}Name cannot be empty. "
            f"Please enter your full name: {Colors.RESET}"
        )
        name = input(prompt).strip()

    return name


def _prompt_for_email() -> str:
    """Prompt user for their email address with validation.

    Returns:
        str: The user's email address
    """
    prompt = f"{Colors.BLUE}Enter your email address (for Git commits): {Colors.RESET}"
    email = input(prompt).strip()

    while not email or "@" not in email:
        prompt = f"{Colors.YELLOW}Please enter a valid email address: {Colors.RESET}"
        email = input(prompt).strip()

    return email


def _apply_git_config(name: str, email: str) -> None:
    """Apply Git configuration settings.

    Args:
        name: User's full name
        email: User's email address
    """
    # Set user information
    run_command(f'git config --global user.name "{name}"')
    run_command(f'git config --global user.email "{email}"')

    # Set sensible defaults
    run_command("git config --global init.defaultBranch main")
    run_command("git config --global pull.rebase false")

    # Display confirmation
    print_success("Git configuration updated:")
    print_success(f"  Name: {name}")
    print_success(f"  Email: {email}")
    print_info("  Default branch: main")
    print_info("  Pull strategy: merge (not rebase)")
