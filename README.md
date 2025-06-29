# Mac Setup

Automated macOS development environment setup script.

## Quick Start

```bash
git clone <your-repo-url> mac-setup
cd mac-setup
./setup.py
```

## What It Installs

### Development Tools

- **Homebrew** - Package manager
- **Node.js** - Via NVM (Node Version Manager)
- **pnpm** - Fast package manager via Corepack
- **Python** - Via pyenv
- **uv** - Fast Python package installer
- **pipx** - Python application manager
- **Docker** - Via Colima (lightweight VM)

### Terminal & Shell

- **iTerm2** - Terminal emulator
- **Oh My Zsh** - Shell framework
- **Atuin** - Shell history sync
- **fzf** - Fuzzy finder
- **autojump** - Directory navigation
- **zsh-autosuggestions** - Command suggestions

### Applications

- VS Code, Chrome, Raycast, Obsidian, and more
- Mac App Store apps (Magnet, Amphetamine, MS Office, KakaoTalk)

### Configuration

- SSH key generation with secure password
- Weekly SSH backup to iCloud
- Korean/English key remapping
- Custom shell aliases

## Features

- **Idempotent**: Safe to run multiple times
- **Auto-cleanup**: Removes old configurations before applying new ones
- **Manual steps**: Prompts for configuration that requires user input
- **Progress tracking**: Clear status messages throughout

## Requirements

- macOS (Apple Silicon or Intel)
- Admin access (for some installations)
- Internet connection

## Customization

Edit `setup.py` to add/remove tools or change configurations.
