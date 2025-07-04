#!/usr/bin/env python3
"""Mac setup script - Install and configure development tools."""


import utils

utils.cleanup_auto_generated_blocks()  # Clean up all auto-generated blocks from .zshrc
utils.clear_crontab()  # Clear crontab to start fresh


# Install Homebrew
utils.install_homebrew()


# Setup Node.js and NVM
utils.setup_nvm_and_node_lts()
utils.setup_pnpm()


# Setup Python environment
utils.setup_pyenv()
utils.setup_uv()
utils.setup_pipx()


# Setup Docker and Colima
utils.setup_docker_cli_colima()


utils.setup_korean_english_key_remapping()


# Setup iTerm2, Zsh, CLI tools, and plugins
utils.install_brew_package("iterm2", "cask")
utils.setup_oh_my_zsh()
utils.setup_zsh_autosuggestions()
utils.setup_fzf()
utils.setup_fast_syntax_highlighting()
utils.setup_atuin()
utils.setup_custom_aliases()
utils.setup_iterm2_natural_text_editing()
utils.install_brew_package("autojump")
utils.install_brew_package("gh")
utils.setup_h_cli()  # h-cli. my custom cli tool.


# Setup zsh plugins
utils.align_zsh_plugins(
    [
        "git",
        "macos",
        "autojump",
        "fast-syntax-highlighting",
    ]
)


# Setup Git and SSH
utils.setup_git_config()
utils.setup_ssh_key()
utils.setup_ssh_backup_cron()


# tools
utils.install_brew_package("mas")  # Mac App Store CLI


utils.install_brew_package("visual-studio-code", "cask")
utils.install_brew_package("font-d2coding", "cask")
utils.install_brew_package("google-chrome", "cask")
utils.install_brew_package("raycast", "cask")  # Spotlight replacement
utils.install_brew_package("jordanbaird-ice", "cask")  # Menu bar management
utils.install_brew_package("maccy", "cask")  # Clipboard manager
utils.install_brew_package("aldente", "cask")  # Battery charge limiter
utils.install_brew_package("obsidian", "cask")  # Note-taking
utils.install_brew_package("alt-tab", "cask")  # Windows-style alt-tab
utils.install_brew_package("keka", "cask")  # File archiver
utils.install_brew_package("appcleaner", "cask")  # Uninstall apps completely
utils.install_brew_package("google-drive", "cask")
utils.install_brew_package("shottr", "cask")  # Screenshot tool
utils.install_brew_package("kap", "cask")  # Screen recording tool
utils.install_brew_package("watchman")  # File watcher for development tools(expo)
utils.install_brew_package("discord", "cask")  # Communication tool
utils.install_brew_package("notion", "cask")  # Note-taking and collaboration

# utils
utils.install_mas_app("441258766", "Magnet")  # Window manager
utils.install_mas_app("937984704", "Amphetamine")  # Keep Mac awake
utils.install_mas_app("869223134", "KakaoTalk")
utils.install_mas_app("462054704", "Microsoft Word")
utils.install_mas_app("462058435", "Microsoft Excel")
utils.install_mas_app("462062816", "Microsoft PowerPoint")


# Development tools

utils.install_brew_package("android-studio", "cask")  # Android development
utils.install_mas_app("497799835", "Xcode")
utils.append_shell_section(
    "Android SDK",
    [
        "export ANDROID_HOME=$HOME/Library/Android/sdk",
        "export PATH=$PATH:$ANDROID_HOME/emulator",
        "export PATH=$PATH:$ANDROID_HOME/platform-tools",
    ],
)
