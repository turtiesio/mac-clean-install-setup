#!/usr/bin/env python3
"""Utility functions and classes for Mac setup scripts - Single import interface."""

# Import everything from app utilities
from utils_app import setup_git_config, setup_h_cli, setup_korean_english_key_remapping

# Import everything from core utilities
from utils_core import (
    Colors,
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
    run_command,
    setup_cron_job,
)

# Import everything from installation utilities
from utils_install import (
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

# Import everything from ssh utilities
from utils_ssh import setup_ssh_backup_cron, setup_ssh_key

# Import everything from zsh utilities
from utils_zsh import (
    align_zsh_plugins,
    setup_atuin,
    setup_authjump,
    setup_custom_aliases,
    setup_fast_syntax_highlighting,
    setup_fzf,
    setup_iterm2_natural_text_editing,
    setup_oh_my_zsh,
    setup_zsh_autosuggestions,
)

# Make all imports available at module level
__all__ = [
    # Core utilities
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
    # Installation utilities
    "install_homebrew",
    "install_brew_package",
    "install_mas_app",
    "setup_nvm_and_node_lts",
    "setup_pnpm",
    "setup_pyenv",
    "setup_uv",
    "setup_pipx",
    "setup_docker_cli_colima",
    # ZSH utilities
    "setup_oh_my_zsh",
    "setup_zsh_autosuggestions",
    "setup_fzf",
    "setup_authjump",
    "setup_fast_syntax_highlighting",
    "setup_atuin",
    "setup_custom_aliases",
    "align_zsh_plugins",
    "setup_iterm2_natural_text_editing",
    # SSH utilities
    "setup_ssh_key",
    "setup_ssh_backup_cron",
    # App utilities
    "setup_korean_english_key_remapping",
    "setup_h_cli",
    "setup_git_config",
]
