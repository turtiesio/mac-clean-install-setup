# Mac Setup

Automated macOS development environment setup script with advanced features for managing shell plugins, cron jobs, and system configurations.

## Quick Start

```bash
git clone <your-repo-url> mac-setup
cd mac-setup
./setup.py
```

## Core Features

### 🔌 Zsh Plugin Management

- Automatically configures Oh My Zsh plugins
- Aligns and maintains plugin list consistency
- Pre-configured plugins: `git`, `macos`, `autojump`, `fast-syntax-highlighting`
- Clean plugin installation without duplicates

### ⏰ Cron Job Management

- Automated SSH key backup to iCloud (weekly)
- Clean crontab management with auto-generated blocks
- Safe cleanup of existing cron jobs before new setup

### 📱 Mac App Store Integration

- Installs Mac App Store apps via `mas` CLI
- Pre-configured apps:
  - Magnet (window manager)
  - Amphetamine (keep Mac awake)
  - Microsoft Office suite
  - KakaoTalk (messaging)

### 🔧 Advanced Shell Configuration

- Custom aliases for common commands
- Shell history sync with Atuin
- Fast syntax highlighting
- Command autosuggestions
- Natural text editing in iTerm2

## What It Installs

### Development Environment

- **Package Managers**

  - Homebrew (system packages)
  - NVM + Node.js LTS
  - pnpm (via Corepack)
  - pyenv + Python
  - uv (fast Python packages)
  - pipx (Python apps)

- **Development Tools**
  - Visual Studio Code
  - GitHub CLI (`gh`)
  - Docker (via Colima)
  - Git configuration

### Terminal Setup

- **iTerm2** with natural text editing
- **Oh My Zsh** with curated plugins
- **Shell Enhancements**
  - fzf (fuzzy finder)
  - autojump (smart directory navigation)
  - Atuin (shell history sync)
  - zsh-autosuggestions
  - fast-syntax-highlighting

### Applications

**Via Homebrew Cask:**

- Google Chrome
- Raycast (Spotlight replacement)
- Ice (menu bar manager)
- Maccy (clipboard manager)
- AlDente (battery charge limiter)
- Obsidian (note-taking)
- Alt-Tab (Windows-style switcher)
- Keka (file archiver)
- AppCleaner
- Google Drive

**Via Mac App Store:**

- Magnet (window management)
- Amphetamine (prevent sleep)
- Microsoft Word, Excel, PowerPoint
- KakaoTalk

### System Configuration

- **SSH Setup**

  - Generates ED25519 SSH key with secure passphrase
  - Weekly automated backup to iCloud via cron
  - Proper permissions and ssh-agent configuration

- **Keyboard & Input**

  - Korean/English key remapping (Right Cmd → 한/영)
  - Natural text editing keybindings

- **Git Configuration**
  - Global user setup
  - Common aliases
  - Sensible defaults

## Features

- **🔄 Idempotent**: Safe to run multiple times
- **🧹 Auto-cleanup**: Removes old configurations before applying new ones
- **📝 Auto-generated blocks**: Manages configuration sections automatically
- **🎯 Progress tracking**: Clear status messages throughout
- **🔐 Secure**: Prompts for passwords and sensitive information

## Requirements

- macOS (Apple Silicon or Intel)
- Admin access (for some installations)
- Internet connection

## Customization

Edit `setup.py` to:

- Add/remove applications
- Modify shell plugins
- Change cron schedules
- Adjust system configurations
