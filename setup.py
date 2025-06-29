#!/usr/bin/env python3
"""Mac setup script - Install and configure development tools."""


from utils import (
    print_info,
    setup_pnpm,
    cleanup_auto_generated_blocks,
    clear_crontab,
    install_homebrew,
    install_brew_package,
    install_mas_app,
    setup_nvm_and_node_lts,
    setup_pyenv,
    setup_uv,
    setup_pipx,
    setup_oh_my_zsh,
    setup_docker_cli_colima,
    setup_korean_english_key_remapping,
    setup_iterm2_natural_text_editing,
    setup_zsh_autosuggestions,
    setup_fzf,
    setup_fast_syntax_highlighting,
    setup_atuin,
    setup_h_cli,
    setup_custom_aliases,
    setup_ssh_key,
    setup_ssh_backup_cron,
    align_zsh_plugins,
)

print_info("Mac 개발 환경 설정 시작")


cleanup_auto_generated_blocks()  # Clean up all auto-generated blocks from .zshrc
clear_crontab()  # Clear crontab to start fresh


# Install Homebrew
install_homebrew()


# Setup Node.js and NVM
setup_nvm_and_node_lts()
setup_pnpm()


# Setup Python environment
setup_pyenv()
setup_uv()
setup_pipx()


# Setup Docker and Colima
setup_docker_cli_colima()


# tools
install_brew_package("mas")  # Mac App Store CLI
install_brew_package("visual-studio-code", "cask")
install_brew_package("font-d2coding", "cask")
install_brew_package("google-chrome", "cask")
install_brew_package("raycast", "cask")  # Spotlight replacement
install_brew_package("jordanbaird-ice", "cask")  # Menu bar management
install_brew_package("maccy", "cask")  # Clipboard manager
install_brew_package("aldente", "cask")  # Battery charge limiter
install_brew_package("obsidian", "cask")  # Note-taking
install_brew_package("alt-tab", "cask")  # Windows-style alt-tab
install_brew_package("keka", "cask")  # File archiver
install_brew_package("appcleaner", "cask")  # Uninstall apps completely
install_brew_package("google-drive", "cask")

# Mac App Store apps
print_info("Installing Mac App Store apps...")
install_mas_app("441258766", "Magnet")  # Window manager
install_mas_app("937984704", "Amphetamine")  # Keep Mac awake
install_mas_app("462054704", "Microsoft Word")
install_mas_app("462058435", "Microsoft Excel")
install_mas_app("462062816", "Microsoft PowerPoint")
install_mas_app("869223134", "KakaoTalk")  # Korean messaging app

setup_korean_english_key_remapping()


print_info("iTerm2 설치")
install_brew_package("iterm2", "cask")
setup_oh_my_zsh()
setup_zsh_autosuggestions()
setup_fzf()
setup_fast_syntax_highlighting()
setup_atuin()
setup_custom_aliases()
setup_iterm2_natural_text_editing()
install_brew_package("autojump")

setup_h_cli()


align_zsh_plugins(
    [
        "git",
        "macos",
        "autojump",
        "fast-syntax-highlighting",
    ]
)

# Setup SSH key and backup
setup_ssh_key()
setup_ssh_backup_cron()
