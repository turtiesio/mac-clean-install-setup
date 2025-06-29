#!/usr/bin/env python3
"""Utility functions and classes for Mac setup scripts."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional


class Colors:
    """Terminal color codes for pretty output."""

    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


def print_success(message: str):
    """Print a success message with green checkmark."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def print_error(message: str):
    """Print an error message with red X."""
    print(f"{Colors.RED}✗{Colors.RESET} {message}")


def print_info(message: str):
    """Print an info message with blue arrow."""
    print(f"{Colors.BLUE}→{Colors.RESET} {message}")


def print_warning(message: str):
    """Print a warning message with yellow exclamation."""
    print(f"{Colors.YELLOW}!{Colors.RESET} {message}")


def cleanup_auto_generated_blocks(file_path: str = "") -> None:
    """Remove all auto-generated blocks from shell config file."""
    config_path = Path(file_path or f"{os.environ['HOME']}/.zshrc")

    if not config_path.exists():
        return

    content = config_path.read_text().splitlines()
    new_content = []
    skip = False

    for line in content:
        if "###### START(AUTO-GENERATED DO NOT EDIT) ######" in line:
            skip = True
        elif "###### END(AUTO-GENERATED DO NOT EDIT) ######" in line:
            skip = False
        elif not skip:
            new_content.append(line)

    # Remove consecutive empty lines
    final = []
    for i, line in enumerate(new_content):
        if line or (i == 0 or (i > 0 and new_content[i - 1])):
            final.append(line)

    config_path.write_text("\n".join(final) + "\n")
    print_success(f"Cleaned up auto-generated blocks from {config_path}")


def append_shell_section(
    description: str, lines: List[str], file_path: str = ""
) -> None:
    """Append a configuration section with START/END markers to shell config file."""
    config_path = Path(file_path or f"{os.environ['HOME']}/.zshrc")
    start_marker = f"# {description} ###### START(AUTO-GENERATED DO NOT EDIT) ######"
    end_marker = f"# {description} ###### END(AUTO-GENERATED DO NOT EDIT) ######"

    # Read current content
    content = config_path.read_text() if config_path.exists() else ""

    # Simply append the new section
    if content and not content.endswith("\n"):
        content += "\n"
    if content and not content.endswith("\n\n"):
        content += "\n"

    content += start_marker + "\n"
    content += "\n".join(lines) + "\n"
    content += end_marker + "\n"

    config_path.write_text(content)
    print_success(f"Added section to {config_path}: {description}")


def run_command(cmd: str, check: bool = True) -> Optional[str]:
    """Run a shell command with error handling."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=True,
            text=True,
            executable="/bin/zsh",
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except subprocess.CalledProcessError:
        if check:
            raise
        return None


def command_exists(command: str) -> bool:
    return run_command(f"which {command}", False) != ""


def get_completion_flag_path(flag_name: str) -> Path:
    """Get the path for a completion flag file."""
    temp_dir = Path(tempfile.gettempdir()) / "mac-setup-flags"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir / f"{flag_name}.completed"


def is_step_completed(flag_name: str) -> bool:
    """Check if a manual configuration step has been completed."""
    flag_path = get_completion_flag_path(flag_name)
    return flag_path.exists()


def mark_step_completed(flag_name: str) -> None:
    """Mark a manual configuration step as completed."""
    flag_path = get_completion_flag_path(flag_name)
    flag_path.touch()
    print_success(f"Marked {flag_name} as completed")


def install_homebrew() -> None:
    # Configure Homebrew in shell
    append_shell_section(
        "Homebrew setup",
        ['eval "$(/opt/homebrew/bin/brew shellenv)"'],
        f"{os.environ['HOME']}/.zprofile",
    )

    if command_exists("brew"):
        print_success("Homebrew is already installed")
        return

    print_info("Installing Homebrew...")
    run_command(
        '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    )

    # Load Homebrew for current session
    run_command('eval "$(/opt/homebrew/bin/brew shellenv)"')
    print_success("Homebrew installed successfully")


def install_brew_package(package: str, package_type: str = "formula") -> bool:
    """Install a single Homebrew package or cask.

    Args:
        package: Package name to install
        package_type: Either 'formula' or 'cask'

    Returns:
        True if installation successful, False otherwise
    """
    # Check if package is already installed
    list_cmd = "brew list"
    if package_type == "cask":
        list_cmd += " --cask"

    try:
        installed_packages = run_command(list_cmd)
        if installed_packages and package in installed_packages.split():
            print_success(f"{package} is already installed")
            return True
    except:
        # If listing fails, continue with installation attempt
        pass

    cmd = "brew install"
    if package_type == "cask":
        cmd += " --cask"
    cmd += f" {package}"

    print_info(f"Installing {package}...")
    result = run_command(cmd)

    if result is not None:
        print_success(f"Installed {package}")
        return True
    else:
        print_error(f"Failed to install {package}")
        return False


# Cache for mas installed apps
_mas_installed_apps_cache = None


def install_mas_app(app_id: str, app_name: str) -> bool:
    """Install a Mac App Store app using mas CLI.

    Args:
        app_id: The numeric ID of the app in Mac App Store
        app_name: Human-readable name of the app for logging

    Returns:
        True if installation successful, False otherwise
    """
    global _mas_installed_apps_cache

    # First check if mas is installed
    if not command_exists("mas"):
        print_error("mas CLI is not installed. Please install it first.")
        return False

    # Load installed apps list once
    if _mas_installed_apps_cache is None:
        _mas_installed_apps_cache = run_command("mas list") or ""

    # Check if already installed
    if app_id in _mas_installed_apps_cache:
        print_success(f"{app_name} is already installed")
        return True

    print_info(f"Installing {app_name} from Mac App Store...")
    result = run_command(f"mas install {app_id}", check=False)

    if result is not None:
        print_success(f"Installed {app_name}")
        # Update cache
        _mas_installed_apps_cache = run_command("mas list") or _mas_installed_apps_cache
        return True
    else:
        print_error(f"Failed to install {app_name}")
        return False


def setup_nvm_and_node_lts() -> None:
    """Setup Node Version Manager and install Node.js LTS."""
    print_info("Setting up NVM...")

    # Create nvm directory
    nvm_dir = Path(f"{os.environ['HOME']}/.nvm")
    nvm_dir.mkdir(exist_ok=True)

    # Configure NVM in shell (in case it's get deleted somehow - prob by the user)
    append_shell_section(
        "NVM (Node Version Manager) setup",
        [
            'export NVM_DIR="$HOME/.nvm"',
            '[ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \\. "/opt/homebrew/opt/nvm/nvm.sh"',
            '[ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && \\. "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"',
        ],
    )

    # Install nvm via Homebrew
    install_brew_package("nvm")

    print_success("NVM configuration added")

    # Install LTS Node version using nvm
    nvm_script = """
    export NVM_DIR="$HOME/.nvm"
    [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \\. "/opt/homebrew/opt/nvm/nvm.sh"
    nvm install --lts
    """
    run_command(nvm_script)

    print_info(
        "NVM installed and configured. Please run 'source ~/.zshrc' in your terminal to use nvm."
    )


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


def create_launch_agent(name: str, plist_content: str) -> None:
    """Create a macOS LaunchAgent plist file.

    Args:
        name: Name of the launch agent (e.g., 'com.example.MyAgent')
        plist_content: The XML content of the plist file
    """
    launch_agent_dir = Path(f"{os.environ['HOME']}/Library/LaunchAgents")
    launch_agent_dir.mkdir(parents=True, exist_ok=True)

    launch_agent_path = launch_agent_dir / f"{name}.plist"
    launch_agent_path.write_text(plist_content)

    print_success(f"Created LaunchAgent: {launch_agent_path}")


def setup_docker_cli_colima() -> None:
    """Setup Docker CLI with Colima (4 CPUs and 8GB memory)."""
    print_info("Setting up Docker CLI with Colima...")

    # Install docker CLI
    install_brew_package("docker", "formula")
    install_brew_package("docker-compose", "formula")

    # Install colima
    install_brew_package("colima", "formula")

    # Check if colima is already running
    colima_status = run_command("colima status", check=False)
    if colima_status and "Running" in colima_status:
        print_success("Colima is already running")
        return

    print_info("Starting Colima with 4 CPUs and 8GB memory...")

    # Start colima with specific configuration
    run_command("colima start --cpu 4 --memory 8")

    print_success("Docker CLI and Colima configured (4 CPUs, 8GB memory)")


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


def setup_pnpm() -> None:
    """Install pnpm using Corepack."""
    print_info("Setting up pnpm...")

    # Update Corepack and enable pnpm
    run_command("npm install --global corepack@latest", check=False)
    run_command("corepack enable pnpm", check=False)
    run_command("corepack prepare pnpm@latest --activate", check=False)

    # Verify installation
    version = run_command("pnpm --version", check=False)
    if version:
        print_success(f"pnpm {version} installed")
    else:
        print_warning("pnpm installation may require a terminal restart")


def setup_pyenv() -> None:
    """Setup pyenv for Python version management."""
    print_info("Setting up pyenv...")

    # Install pyenv
    install_brew_package("pyenv")

    # Configure pyenv in shell
    append_shell_section(
        "pyenv setup",
        [
            'export PYENV_ROOT="$HOME/.pyenv"',
            '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"',
            'eval "$(pyenv init -)"',
        ],
    )

    print_success("pyenv installed successfully")
    print_info("Run 'pyenv install -l' to see available Python versions")


def setup_uv() -> None:
    """Install uv - Fast Python package installer."""
    if command_exists("uv"):
        print_success("uv is already installed")
        return

    print_info("Installing uv...")
    run_command("curl -LsSf https://astral.sh/uv/install.sh | sh")

    print_success("uv installed successfully")


def setup_pipx() -> None:
    """Install pipx for Python application management."""
    print_info("Setting up pipx...")

    # Install pipx
    install_brew_package("pipx")

    # Ensure pipx paths are set up
    run_command("pipx ensurepath")

    print_success("pipx installed successfully")
    print_info("You can now install Python applications with 'pipx install'")


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
            import shutil

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


def clear_crontab() -> bool:
    """Clear all cron jobs for the current user.

    Returns:
        True if crontab was cleared successfully, False otherwise
    """
    print_info("Clearing crontab...")

    # Check if there's an existing crontab
    existing = run_command("crontab -l 2>/dev/null", check=False)
    if not existing:
        print_success("Crontab is already empty")
        return True

    # Clear the crontab
    result = run_command("crontab -r 2>/dev/null", check=False)
    if result is not None or run_command("crontab -l 2>/dev/null", check=False) is None:
        print_success("Crontab cleared successfully")
        return True
    else:
        print_error("Failed to clear crontab")
        return False


def setup_cron_job(
    schedule: str, command: str, description: str = "", check_exists: bool = True
) -> bool:
    """Setup a cron job.

    Args:
        schedule: Cron schedule expression (e.g., "0 9 * * *" for daily at 9am)
        command: Command to execute
        description: Optional description comment for the cron job
        check_exists: Check if similar job already exists

    Returns:
        True if cron job was added successfully, False otherwise

    Example:
        setup_cron_job("0 9 * * *", "/usr/bin/python3 /path/to/script.py", "Daily backup")
    """
    print_info(f"Setting up cron job: {description or command}")

    # Get current crontab
    current_crontab = run_command("crontab -l 2>/dev/null", check=False) or ""

    # Check if job already exists
    if check_exists and command in current_crontab:
        print_success("Cron job already exists")
        return True

    # Prepare new cron entry
    cron_entry = ""
    if description:
        cron_entry += f"# {description}\n"
    cron_entry += f"{schedule} {command}\n"

    # Create temporary file with updated crontab
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        if current_crontab and not current_crontab.endswith("\n"):
            current_crontab += "\n"
        tmp.write(current_crontab)
        tmp.write(cron_entry)
        tmp_path = tmp.name

    try:
        # Install new crontab
        result = run_command(f"crontab {tmp_path}", check=False)
        if result is not None:
            print_success(f"Cron job added: {schedule} {command}")
            return True
        else:
            print_error("Failed to install cron job")
            return False
    finally:
        # Clean up temporary file
        Path(tmp_path).unlink(missing_ok=True)


def _add_key_to_agent_with_password(key_path: Path, password: str) -> bool:
    """Add SSH key to agent using SSH_ASKPASS mechanism."""
    import tempfile

    # Create askpass script
    askpass_script = f"""#!/bin/bash
echo '{password}'
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as tmp:
        tmp.write(askpass_script)
        askpass_path = tmp.name

    try:
        os.chmod(askpass_path, 0o700)

        # Add to ssh-agent using SSH_ASKPASS
        env = os.environ.copy()
        env["DISPLAY"] = "1"
        env["SSH_ASKPASS"] = askpass_path
        env["SSH_ASKPASS_REQUIRE"] = "force"

        result = subprocess.run(
            ["ssh-add", "--apple-use-keychain", str(key_path)],
            env=env,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    finally:
        Path(askpass_path).unlink(missing_ok=True)


def _setup_ssh_config(ssh_dir: Path) -> None:
    """Setup SSH config for GitHub and general usage."""
    config_file = ssh_dir / "config"

    # SSH config with macOS keychain integration
    ssh_config = """# Configured by mac-setup
Host *
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519
  ServerAliveInterval 60
  ServerAliveCountMax 3
"""

    if config_file.exists():
        existing_config = config_file.read_text()
        # Check if we already configured this
        if "# Configured by mac-setup" not in existing_config:
            # Append our config to existing
            if existing_config and not existing_config.endswith("\n"):
                existing_config += "\n"
            config_file.write_text(existing_config + "\n" + ssh_config)
            print_info("Added SSH config to existing file")
        else:
            print_info("SSH config already configured by mac-setup")
    else:
        config_file.write_text(ssh_config)
        print_info("Created new SSH config")

    # Ensure proper permissions
    config_file.chmod(0o600)


def _add_existing_key_to_agent(key_path: Path) -> None:
    """Add an existing SSH key to ssh-agent, prompting for password if needed."""
    # Start ssh-agent if needed
    run_command('eval "$(ssh-agent -s)"', check=False)

    # Check if key is already in agent by comparing fingerprints
    agent_keys = run_command("ssh-add -l", check=False)
    if agent_keys:
        # Get fingerprint of the key file
        key_fingerprint = run_command(f"ssh-keygen -lf {key_path}", check=False)
        if key_fingerprint:
            # Extract just the fingerprint part (second field)
            fingerprint = (
                key_fingerprint.split()[1] if len(key_fingerprint.split()) > 1 else ""
            )
            if fingerprint and fingerprint in agent_keys:
                print_success(f"{key_path.name} is already in ssh-agent")
                return

    print_info(f"Adding {key_path.name} to ssh-agent...")

    # Check if key has a passphrase by trying to load it
    result = subprocess.run(
        ["ssh-keygen", "-y", "-f", str(key_path)], capture_output=True, text=True
    )

    if result.returncode != 0:
        # Key has passphrase, prompt for it
        print(
            f"{Colors.YELLOW}This SSH key is protected by a passphrase.{Colors.RESET}"
        )
        password = input(
            f"{Colors.BLUE}Enter passphrase for {key_path.name}: {Colors.RESET}"
        )

        if _add_key_to_agent_with_password(key_path, password):
            print_success(f"{key_path.name} added to ssh-agent with keychain")
        else:
            print_warning(
                f"Could not add {key_path.name} to ssh-agent. You may need to add it manually."
            )
    else:
        # No passphrase, add directly
        result = subprocess.run(
            ["ssh-add", "--apple-use-keychain", str(key_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print_success(f"{key_path.name} added to ssh-agent")
        else:
            print_warning(f"Could not add {key_path.name} to ssh-agent")


def setup_ssh_key() -> None:
    """Generate a new SSH key with secure password and configure ssh-agent."""
    print_info("Setting up SSH key...")

    # Check for existing SSH keys
    ssh_dir = Path(f"{os.environ['HOME']}/.ssh")
    ssh_dir.mkdir(mode=0o700, exist_ok=True)

    # Check if default key already exists
    if (ssh_dir / "id_ed25519").exists():
        print_success("SSH key already exists at ~/.ssh/id_ed25519")
        # Try to add to ssh-agent
        _add_existing_key_to_agent(ssh_dir / "id_ed25519")
        return

    # Check for SSH backups in iCloud
    backup_dir = Path(
        f"{os.environ['HOME']}/Library/Mobile Documents/com~apple~CloudDocs/Backup/ssh"
    )
    if backup_dir.exists():
        backups = sorted(backup_dir.glob("ssh_backup_*.zip"), reverse=True)
        if backups:
            print_info(f"Found {len(backups)} SSH backup(s) in iCloud")
            print(f"\n{Colors.BLUE}Most recent backup:{Colors.RESET} {backups[0].name}")

            response = input(
                f"{Colors.YELLOW}Would you like to restore from backup? (yes/no): {Colors.RESET}"
            ).lower()

            if response == "yes":
                print_info("Restoring SSH keys from backup...")

                # Extract backup
                import zipfile

                with zipfile.ZipFile(backups[0], "r") as zip_ref:
                    # Extract to home directory (will create .ssh folder)
                    zip_ref.extractall(os.environ["HOME"])

                # Fix permissions
                ssh_dir.chmod(0o700)
                for file in ssh_dir.iterdir():
                    if file.name.startswith("id_"):
                        if file.name.endswith(".pub"):
                            file.chmod(0o644)
                        else:
                            file.chmod(0o600)

                print_success("SSH keys restored from backup")

                # Try to add to ssh-agent
                for key_file in ssh_dir.glob("id_*"):
                    if not key_file.name.endswith(".pub"):
                        _add_existing_key_to_agent(key_file)

                return

    # Generate secure random password
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = "".join(secrets.choice(alphabet) for _ in range(32))

    print("\n" + "=" * 60)
    print(f"{Colors.YELLOW}⚠️  IMPORTANT: SAVE THIS PASSWORD ⚠️{Colors.RESET}")
    print("=" * 60)
    print(f"\n{Colors.BLUE}Generated secure SSH key password:{Colors.RESET}")
    print(f"\n{Colors.GREEN}{password}{Colors.RESET}\n")
    print(
        f"{Colors.YELLOW}Please save this password in your password manager NOW!{Colors.RESET}"
    )
    print("You will need it when using this SSH key.")
    print("=" * 60 + "\n")

    response = input(
        f"{Colors.YELLOW}Type 'saved' when you have saved this password: {Colors.RESET}"
    )
    while response.lower() != "saved":
        response = input(
            f"{Colors.YELLOW}Please type 'saved' to confirm you've saved the password: {Colors.RESET}"
        )

    # Get user email
    email = input(
        f"{Colors.BLUE}Enter your email address for the SSH key (used for Git commits): {Colors.RESET}"
    )

    # Generate SSH key without passphrase first
    print_info(f"Generating ED25519 SSH key...")
    key_path = ssh_dir / "id_ed25519"

    # Generate key without passphrase initially
    subprocess.run(
        ["ssh-keygen", "-t", "ed25519", "-C", email, "-f", str(key_path), "-N", ""],
        check=True,
    )

    # Now add passphrase to the key
    print_info("Adding passphrase to SSH key...")
    subprocess.run(
        ["ssh-keygen", "-p", "-f", str(key_path), "-N", password, "-P", ""],
        check=True,
        capture_output=True,
    )

    # Configure SSH config
    _setup_ssh_config(ssh_dir)

    # Start ssh-agent and add key
    print_info("Adding SSH key to ssh-agent...")
    run_command('eval "$(ssh-agent -s)"')

    # Add key with password
    if _add_key_to_agent_with_password(key_path, password):
        print_success("SSH key added to ssh-agent with keychain")
    else:
        print_warning("Failed to add SSH key to agent")

    # Display public key
    public_key = run_command("cat ~/.ssh/id_ed25519.pub")
    print("\n" + "=" * 60)
    print(f"{Colors.GREEN}✓ SSH key generated successfully!{Colors.RESET}")
    print("=" * 60)
    print(f"\n{Colors.BLUE}Your SSH public key:{Colors.RESET}\n")
    print(public_key)

    # Copy to clipboard if pbcopy is available
    if command_exists("pbcopy"):
        run_command("cat ~/.ssh/id_ed25519.pub | pbcopy")
        print(f"\n{Colors.GREEN}✓ Public key copied to clipboard!{Colors.RESET}")

    # Prompt user to add to GitHub
    print("\n" + "=" * 60)
    print(f"{Colors.YELLOW}⚠️  MANUAL CONFIGURATION REQUIRED ⚠️{Colors.RESET}")
    print("=" * 60)
    print(f"\n{Colors.BLUE}Add your SSH key to GitHub:{Colors.RESET}")
    print("  1. The public key has been copied to your clipboard")
    print("  2. Open GitHub SSH settings: https://github.com/settings/keys")
    print("  3. Click 'New SSH key'")
    print("  4. Give it a title (e.g., 'MacBook Pro')")
    print("  5. Paste the key and click 'Add SSH key'")
    print("\n  Note: The key is already added to your SSH agent with keychain.")
    print("=" * 60 + "\n")

    response = input(
        f"{Colors.YELLOW}Type 'done' when you have added the key to GitHub: {Colors.RESET}"
    )
    while response.lower() != "done":
        response = input(
            f"{Colors.YELLOW}Please type 'done' to continue: {Colors.RESET}"
        )

    # Test the connection
    print_info("Testing SSH connection to GitHub...")

    # First, add GitHub to known hosts if not already there
    known_hosts_file = ssh_dir / "known_hosts"
    if (
        not known_hosts_file.exists()
        or "github.com" not in known_hosts_file.read_text()
    ):
        print_info("Adding GitHub to known hosts...")
        run_command(
            "ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts", check=False
        )

    # Now test the connection
    test_result = run_command("ssh -T git@github.com 2>&1", check=False)
    if test_result and "successfully authenticated" in test_result:
        print_success("GitHub SSH authentication successful!")
    else:
        print_warning("Could not verify GitHub connection.")
        print_info("Try running manually: ssh -T git@github.com")

    print_success("SSH key setup completed")


def setup_ssh_backup_cron() -> None:
    """Setup weekly cron job to backup SSH keys to iCloud."""
    print_info("Setting up SSH backup cron job...")

    # Create backup script
    backup_script = f"""#!/bin/bash
# SSH Backup Script
BACKUP_DIR="{os.environ['HOME']}/Library/Mobile Documents/com~apple~CloudDocs/Backup/ssh"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ZIP_FILE="$BACKUP_DIR/ssh_backup_$TIMESTAMP.zip"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create zip backup of .ssh directory
cd "$HOME" && zip -r "$ZIP_FILE" .ssh/

# Keep only the 4 most recent backups
cd "$BACKUP_DIR" && ls -t ssh_backup_*.zip | tail -n +5 | xargs -r rm

echo "SSH backup completed: $ZIP_FILE"
"""

    # Save backup script
    scripts_dir = Path(f"{os.environ['HOME']}/.local/bin")
    scripts_dir.mkdir(parents=True, exist_ok=True)

    script_path = scripts_dir / "ssh_backup.sh"
    script_path.write_text(backup_script)
    script_path.chmod(0o755)

    # Setup cron job to run weekly on Sunday at 2 AM
    setup_cron_job(
        "0 2 * * 0",  # Weekly on Sunday at 2 AM
        str(script_path),
        "Weekly SSH backup to iCloud",
    )

    print_success("SSH backup cron job configured (weekly on Sundays at 2 AM)")
    print_info(f"Backup script created at: {script_path}")
    print_info(
        "Backups will be saved to: ~/Library/Mobile Documents/com~apple~CloudDocs/Backup/ssh"
    )


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
