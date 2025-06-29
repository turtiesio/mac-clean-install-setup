#!/usr/bin/env python3
"""Application-specific utility functions for Mac setup scripts."""

import os
import shutil
from pathlib import Path

from utils_core import (
    Colors,
    create_launch_agent,
    is_step_completed,
    mark_step_completed,
    print_info,
    print_success,
    print_warning,
    run_command,
)


def setup_korean_english_key_remapping() -> None:
    """Setup Korean-English switching delay configuration."""
    print_info("한영 전환 딜레이 설정")

    # Apply the key remapping
    run_command(
        'hidutil property --set \'{"UserKeyMapping":[{"HIDKeyboardModifierMappingSrc": 0x700000039, "HIDKeyboardModifierMappingDst": 0x70000006D}]}\''
    )

    # Create launch agent to persist the setting
    create_launch_agent(
        "com.example.KeyRemapping",
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
<key>Label</key>
<string>com.example.KeyRemapping</string>
<key>ProgramArguments</key>
<array>
    <string>/usr/bin/hidutil</string>
    <string>property</string>
    <string>--set</string>
    <string>{"UserKeyMapping":[{"HIDKeyboardModifierMappingSrc": 0x700000039, "HIDKeyboardModifierMappingDst": 0x70000006D}]}</string>
</array>
<key>RunAtLoad</key>
<true/>
</dict>
</plist>""",
    )


def setup_h_cli() -> None:
    """Install h-cli from GitHub repository."""
    print_info("Setting up h-cli...")

    # Clone h-cli repository
    h_cli_dir = Path(f"{os.environ['HOME']}/.h-cli")
    if h_cli_dir.exists():
        # Check if there are updates available
        run_command(f"cd {h_cli_dir} && git fetch", check=False)

        # Get the default branch name
        default_branch = run_command(
            f"cd {h_cli_dir} && git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'",
            check=False,
        )
        if not default_branch:
            # Fallback: try to detect from remote branches
            default_branch = "main"
            if (
                run_command(
                    f"cd {h_cli_dir} && git branch -r | grep -q origin/master",
                    check=False,
                )
                is not None
            ):
                default_branch = "master"

        local_hash = run_command(f"cd {h_cli_dir} && git rev-parse HEAD", check=False)
        remote_hash = run_command(
            f"cd {h_cli_dir} && git rev-parse origin/{default_branch}", check=False
        )

        if local_hash and remote_hash and local_hash != remote_hash:
            print_info("Updates available for h-cli...")
            run_command(f"cd {h_cli_dir} && git pull")
            # Reinstall after update
            print_info("Installing h-cli globally...")
            run_command(f"cd {h_cli_dir} && make install-global")
        else:
            print_success("h-cli is already up to date")
            return
    else:
        print_info("Cloning h-cli repository...")
        run_command(f"git clone https://github.com/turtiesio/h-cli.git {h_cli_dir}")
        # Install after clone
        print_info("Installing h-cli globally...")
        run_command(f"cd {h_cli_dir} && make install-global")

    print_success("h-cli installed successfully")

    # Copy default config if not exists
    config_dir = Path(f"{os.environ['HOME']}/.config/h-cli")
    config_file = config_dir / "config.yaml"

    if not config_file.exists():
        print_info("Setting up h-cli configuration...")
        config_dir.mkdir(parents=True, exist_ok=True)

        # Copy from h-cli repo's default config
        default_config = h_cli_dir / "config" / "default.yaml"
        if default_config.exists():
            shutil.copy2(default_config, config_file)
            print_success("Copied default h-cli config")
        else:
            print_warning("Could not find default config in h-cli repository")

    # Prompt for API keys setup
    flag_name = "h_cli_api_keys_configured"
    if not is_step_completed(flag_name):
        print("\n" + "=" * 60)
        print(f"{Colors.YELLOW}⚠️  MANUAL CONFIGURATION REQUIRED ⚠️{Colors.RESET}")
        print("=" * 60)
        print(f"\n{Colors.BLUE}Configure h-cli API keys:{Colors.RESET}")
        print(f"  1. Open config: {config_file}")
        print("  2. Add your API keys:")
        print(
            "     • gemini_api_key: Get from https://makersuite.google.com/app/apikey"
        )
        print("     • openrouter_api_key: Get from https://openrouter.ai/keys")
        print(
            "\n  Note: h-cli will work without API keys but AI features will be limited."
        )
        print("=" * 60 + "\n")

        response = input(
            f"{Colors.YELLOW}Type 'done' when you have added your API keys (or 'skip' to configure later): {Colors.RESET}"
        )
        while response.lower() not in ["done", "skip"]:
            response = input(
                f"{Colors.YELLOW}Please type 'done' or 'skip' to continue: {Colors.RESET}"
            )

        if response.lower() == "done":
            mark_step_completed(flag_name)
            print_success("h-cli API keys configured")
        else:
            print_info(
                "You can configure API keys later by editing: " + str(config_file)
            )

    print_info("You can now use 'h' command. Try 'h --help' to see available commands.")


def setup_git_config() -> None:
    """Setup Git global configuration with user name and email."""
    print_info("Setting up Git configuration...")

    # Check if already configured
    existing_name = run_command("git config --global user.name", check=False)
    existing_email = run_command("git config --global user.email", check=False)

    if existing_name and existing_email:
        print_info(f"Git already configured:")
        print_info(f"  Name: {existing_name}")
        print_info(f"  Email: {existing_email}")

        print_success("Keeping existing Git configuration")
        return

    # Get user input
    print(f"\n{Colors.BLUE}Configure Git global settings:{Colors.RESET}")

    name = input(f"{Colors.BLUE}Enter your full name (for Git commits): {Colors.RESET}")
    while not name.strip():
        name = input(
            f"{Colors.YELLOW}Name cannot be empty. Please enter your full name: {Colors.RESET}"
        )

    email = input(
        f"{Colors.BLUE}Enter your email address (for Git commits): {Colors.RESET}"
    )
    while not email.strip() or "@" not in email:
        email = input(
            f"{Colors.YELLOW}Please enter a valid email address: {Colors.RESET}"
        )

    # Set Git configuration
    run_command(f'git config --global user.name "{name}"')
    run_command(f'git config --global user.email "{email}"')

    # Set other useful defaults
    run_command("git config --global init.defaultBranch main")
    run_command("git config --global pull.rebase false")

    print_success("Git configuration updated:")
    print_success(f"  Name: {name}")
    print_success(f"  Email: {email}")
    print_info("  Default branch: main")
    print_info("  Pull strategy: merge (not rebase)")
