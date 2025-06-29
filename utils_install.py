#!/usr/bin/env python3
"""Installation utility functions for Mac setup scripts."""

import os

from utils_core import (
    append_shell_section,
    command_exists,
    print_error,
    print_info,
    print_success,
    print_warning,
    run_command,
)

# Cache for mas installed apps
_mas_installed_apps_cache = None


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
    from pathlib import Path

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
