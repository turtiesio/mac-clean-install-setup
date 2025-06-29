#!/usr/bin/env python3
"""Central utility module for Mac setup automation.

This module serves as a single import interface for all utility functions
and classes used in the Mac setup scripts. It provides a clean API by
re-exporting functions from specialized utility modules.

The utilities are organized into the following categories:
- Core: Basic functionality like command execution, printing, and state management
- Installation: Package managers and software installation utilities
- Shell (ZSH): Shell configuration and plugin management
- SSH: SSH key generation and backup configuration
- Application: Application-specific setup utilities

Example:
    >>> from utils import print_success, install_homebrew, setup_oh_my_zsh
    >>> print_success("Starting Mac setup...")
    >>> install_homebrew()
    >>> setup_oh_my_zsh()
"""

from typing import List

from .utils_app import (
    setup_git_config,
    setup_h_cli,
    setup_korean_english_key_remapping,
)
from .utils_core import Colors  # Terminal color constants for formatted output
from .utils_core import (  # Output formatting functions; Command execution; State management; File manipulation; System configuration
    append_shell_section,
    cleanup_auto_generated_blocks,
    clear_crontab,
    command_exists,
    create_launch_agent,
    get_completion_flag_path,
    is_step_completed,
    mark_step_completed,
    print_error,
    print_info,
    print_success,
    print_warning,
    prompt_for_user_input,
    run_command,
    setup_cron_job,
)
from .utils_install import (  # Package managers; Development environments
    install_brew_package,
    install_homebrew,
    install_mas_app,
    setup_docker_cli_colima,
    setup_nvm_and_node_lts,
    setup_pipx,
    setup_pnpm,
    setup_pyenv,
    setup_uv,
)
from .utils_ssh import (
    setup_ssh_backup_cron,
    setup_ssh_key,
)
from .utils_zsh import setup_atuin  # Shell history database
from .utils_zsh import setup_autojump  # Directory jumping
from .utils_zsh import setup_fzf  # Fuzzy finder
from .utils_zsh import (  # Core shell setup; Shell plugins and enhancements
    align_zsh_plugins,
    setup_custom_aliases,
    setup_fast_syntax_highlighting,
    setup_iterm2_natural_text_editing,
    setup_oh_my_zsh,
    setup_zsh_autosuggestions,
)

# ============================================================================
# APPLICATION UTILITIES
# ============================================================================
# Functions for configuring specific applications and tools


# ============================================================================
# CORE UTILITIES
# ============================================================================
# Essential functions for command execution, output formatting, and state management


# ============================================================================
# INSTALLATION UTILITIES
# ============================================================================
# Package managers and software installation functions


# ============================================================================
# SSH UTILITIES
# ============================================================================
# SSH key management and backup configuration


# ============================================================================
# ZSH SHELL UTILITIES
# ============================================================================
# Shell configuration, plugins, and enhancements


# ============================================================================
# PUBLIC API
# ============================================================================
# Define all exported symbols for clean imports

__all__: List[str] = [
    # --- Core Utilities ---
    "Colors",
    "print_success",
    "print_error",
    "print_info",
    "print_warning",
    "run_command",
    "command_exists",
    "get_completion_flag_path",
    "is_step_completed",
    "mark_step_completed",
    "cleanup_auto_generated_blocks",
    "append_shell_section",
    "clear_crontab",
    "setup_cron_job",
    "create_launch_agent",
    "prompt_for_user_input",
    # --- Installation Utilities ---
    "install_homebrew",
    "install_brew_package",
    "install_mas_app",
    "setup_nvm_and_node_lts",
    "setup_pnpm",
    "setup_pyenv",
    "setup_uv",
    "setup_pipx",
    "setup_docker_cli_colima",
    # --- ZSH Shell Utilities ---
    "setup_oh_my_zsh",
    "setup_zsh_autosuggestions",
    "setup_fzf",
    "setup_autojump",
    "setup_fast_syntax_highlighting",
    "setup_atuin",
    "setup_custom_aliases",
    "align_zsh_plugins",
    "setup_iterm2_natural_text_editing",
    # --- SSH Utilities ---
    "setup_ssh_key",
    "setup_ssh_backup_cron",
    # --- Application Utilities ---
    "setup_korean_english_key_remapping",
    "setup_h_cli",
    "setup_git_config",
]
