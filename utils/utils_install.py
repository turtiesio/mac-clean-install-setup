#!/usr/bin/env python3
"""
Installation utility functions for Mac setup scripts.

This module provides functions for installing various development tools and
applications on macOS, including Homebrew packages, Mac App Store apps, and
development environments like Node.js, Python, and Docker.
"""

import os
from pathlib import Path
from typing import List, Optional

from .utils_core import (
    append_shell_section,
    command_exists,
    print_error,
    print_info,
    print_success,
    print_warning,
    run_command,
)

# Global cache for Mac App Store installed apps to avoid repeated queries
_mas_installed_apps_cache: Optional[str] = None


def install_homebrew() -> None:
    """
    Install Homebrew package manager if not already installed.

    This function:
    1. Configures Homebrew in the shell profile
    2. Checks if Homebrew is already installed
    3. Downloads and installs Homebrew if needed
    4. Loads Homebrew environment for the current session
    """
    # First, ensure Homebrew is configured in shell profile
    _configure_homebrew_shell()

    if command_exists("brew"):
        print_success("Homebrew is already installed")
        return

    print_info("Installing Homebrew...")

    # Download and run the official Homebrew installation script
    install_script_url = (
        "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"
    )
    run_command(f'/bin/bash -c "$(curl -fsSL {install_script_url})"')

    # Load Homebrew environment for current session
    run_command('eval "$(/opt/homebrew/bin/brew shellenv)"')

    print_success("Homebrew installed successfully")


def _configure_homebrew_shell() -> None:
    """Configure Homebrew in the shell profile for future sessions."""
    homebrew_config = ['eval "$(/opt/homebrew/bin/brew shellenv)"']
    profile_path = f"{os.environ['HOME']}/.zprofile"

    append_shell_section(
        description="Homebrew setup",
        config_lines=homebrew_config,
        config_file_path=profile_path,
    )


def install_brew_package(package: str, package_type: str = "formula") -> bool:
    """
    Install a single Homebrew package or cask.

    Args:
        package: The name of the package to install (e.g., 'git', 'visual-studio-code')
        package_type: Type of package - either 'formula' or 'cask'
                     - 'formula': Command-line tools and libraries
                     - 'cask': GUI applications

    Returns:
        bool: True if installation was successful, False otherwise

    Examples:
        >>> install_brew_package("git")  # Install Git command-line tool
        True
        >>> install_brew_package("visual-studio-code", "cask")  # Install VS Code app
        True
    """
    if not _is_valid_package_type(package_type):
        print_error(
            f"Invalid package type: {package_type}. Must be 'formula' or 'cask'"
        )
        return False

    if _is_package_installed(package, package_type):
        print_success(f"{package} is already installed")
        return True

    return _perform_brew_installation(package, package_type)


def _is_valid_package_type(package_type: str) -> bool:
    """Validate that the package type is either 'formula' or 'cask'."""
    return package_type in ("formula", "cask")


def _is_package_installed(package: str, package_type: str) -> bool:
    """
    Check if a Homebrew package is already installed.

    Args:
        package: Package name to check
        package_type: Either 'formula' or 'cask'

    Returns:
        bool: True if package is installed, False otherwise
    """
    list_command = "brew list"
    if package_type == "cask":
        list_command += " --cask"

    try:
        installed_packages = run_command(list_command)
        if installed_packages and package in installed_packages.split():
            return True
    except Exception:
        # If listing fails, we'll proceed with installation attempt
        pass

    return False


def _perform_brew_installation(package: str, package_type: str) -> bool:
    """
    Perform the actual Homebrew package installation.

    Args:
        package: Package name to install
        package_type: Either 'formula' or 'cask'

    Returns:
        bool: True if installation succeeded, False otherwise
    """
    install_command = "brew install"
    if package_type == "cask":
        install_command += " --cask"
    install_command += f" {package}"

    print_info(f"Installing {package}...")
    result = run_command(install_command)

    if result is not None:
        print_success(f"Installed {package}")
        return True
    else:
        print_error(f"Failed to install {package}")
        return False


def install_mas_app(app_id: str, app_name: str) -> bool:
    """
    Install a Mac App Store application using the mas CLI tool.

    Args:
        app_id: The numeric ID of the app in Mac App Store
                (can be found in the app's URL on the App Store website)
        app_name: Human-readable name of the app for logging purposes

    Returns:
        bool: True if installation was successful, False otherwise

    Examples:
        >>> install_mas_app("497799835", "Xcode")  # Install Xcode
        True
        >>> install_mas_app("1295203466", "Microsoft Remote Desktop")
        True

    Note:
        Requires 'mas' CLI to be installed and user to be signed in to Mac App Store.
    """
    if not _validate_mas_cli():
        return False

    if _is_mas_app_installed(app_id):
        print_success(f"{app_name} is already installed")
        return True

    return _perform_mas_installation(app_id, app_name)


def _validate_mas_cli() -> bool:
    """Check if mas CLI is available."""
    if not command_exists("mas"):
        print_error("mas CLI is not installed. Please install it first.")
        return False
    return True


def _is_mas_app_installed(app_id: str) -> bool:
    """
    Check if a Mac App Store app is already installed.

    Uses a global cache to avoid repeated queries to mas list.
    """
    global _mas_installed_apps_cache

    # Load installed apps list once per session
    if _mas_installed_apps_cache is None:
        _mas_installed_apps_cache = run_command("mas list") or ""

    return app_id in _mas_installed_apps_cache


def _perform_mas_installation(app_id: str, app_name: str) -> bool:
    """
    Perform the actual Mac App Store app installation.

    Args:
        app_id: The numeric ID of the app
        app_name: Human-readable name for logging

    Returns:
        bool: True if installation succeeded, False otherwise
    """
    global _mas_installed_apps_cache

    print_info(f"Installing {app_name} from Mac App Store...")
    result = run_command(f"mas install {app_id}", check=False)

    if result is not None:
        print_success(f"Installed {app_name}")
        # Update cache to reflect new installation
        _mas_installed_apps_cache = run_command("mas list") or _mas_installed_apps_cache
        return True
    else:
        print_error(f"Failed to install {app_name}")
        return False


def setup_nvm_and_node_lts() -> None:
    """
    Set up Node Version Manager (NVM) and install the latest Node.js LTS version.

    This function:
    1. Creates the NVM directory structure
    2. Installs NVM via Homebrew
    3. Configures NVM in the shell profile
    4. Installs the latest Node.js LTS version

    Note:
        After installation, users need to restart their terminal or run
        'source ~/.zshrc' to use NVM commands.
    """
    print_info("Setting up NVM...")

    # Ensure NVM directory exists
    _create_nvm_directory()

    # Configure NVM in shell profile
    _configure_nvm_shell()

    # Install NVM via Homebrew
    install_brew_package("nvm")
    print_success("NVM configuration added")

    # Install Node.js LTS version
    _install_node_lts()

    print_info(
        "NVM installed and configured. Please run 'source ~/.zshrc' in your terminal to use nvm."
    )


def _create_nvm_directory() -> None:
    """Create the NVM directory if it doesn't exist."""
    nvm_dir = Path(f"{os.environ['HOME']}/.nvm")
    nvm_dir.mkdir(exist_ok=True)


def _configure_nvm_shell() -> None:
    """Add NVM configuration to shell profile."""
    nvm_config_lines = [
        'export NVM_DIR="$HOME/.nvm"',
        '[ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \\. "/opt/homebrew/opt/nvm/nvm.sh"',
        '[ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && \\. "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"',
    ]

    append_shell_section(
        description="NVM (Node Version Manager) setup",
        config_lines=nvm_config_lines,
    )


def _install_node_lts() -> None:
    """Install the latest Node.js LTS version using NVM."""
    nvm_script = """
    export NVM_DIR="$HOME/.nvm"
    [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \\. "/opt/homebrew/opt/nvm/nvm.sh"
    nvm install --lts
    """
    run_command(nvm_script)


def setup_pnpm() -> None:
    """
    Install pnpm (performant npm) using Corepack.

    pnpm is a fast, disk space efficient package manager for Node.js.
    This function uses Corepack (included with Node.js 16.13+) to install pnpm.

    Note:
        Requires Node.js to be installed first.
        May require terminal restart for pnpm command to be available.
    """
    print_info("Setting up pnpm...")

    # Update Corepack to latest version
    run_command("npm install --global corepack@latest", check=False)

    # Enable pnpm in Corepack
    run_command("corepack enable pnpm", check=False)

    # Prepare and activate the latest pnpm version
    run_command("corepack prepare pnpm@latest --activate", check=False)

    # Verify installation
    version = run_command("pnpm --version", check=False)
    if version:
        print_success(f"pnpm {version} installed")
    else:
        print_warning("pnpm installation may require a terminal restart")


def setup_pyenv() -> None:
    """
    Set up pyenv for Python version management.

    pyenv allows you to easily switch between multiple versions of Python.
    It's simple, unobtrusive, and follows the UNIX tradition of single-purpose tools.

    After installation, use:
    - 'pyenv install -l' to see available Python versions
    - 'pyenv install 3.x.x' to install a specific version
    - 'pyenv global 3.x.x' to set the global Python version
    """
    print_info("Setting up pyenv...")

    # Install pyenv via Homebrew
    install_brew_package("pyenv")

    # Configure pyenv in shell profile
    _configure_pyenv_shell()

    print_success("pyenv installed successfully")
    print_info("Run 'pyenv install -l' to see available Python versions")


def _configure_pyenv_shell() -> None:
    """Add pyenv configuration to shell profile."""
    pyenv_config_lines = [
        'export PYENV_ROOT="$HOME/.pyenv"',
        '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"',
        'eval "$(pyenv init -)"',
    ]

    append_shell_section(
        description="pyenv setup",
        config_lines=pyenv_config_lines,
    )


def setup_uv() -> None:
    """
    Install uv - An extremely fast Python package installer and resolver.

    uv is a Rust-based Python package installer that's 10-100x faster than pip.
    It's a drop-in replacement for pip and pip-tools, with a focus on performance.

    Features:
    - 10-100x faster than pip
    - Installs packages in parallel
    - Uses a global cache to avoid re-downloading packages
    - Compatible with pip's command-line interface
    """
    if command_exists("uv"):
        print_success("uv is already installed")
        return

    print_info("Installing uv...")

    # Download and run the official uv installation script
    install_script_url = "https://astral.sh/uv/install.sh"
    run_command(f"curl -LsSf {install_script_url} | sh")

    print_success("uv installed successfully")


def setup_pipx() -> None:
    """
    Install pipx for Python application management.

    pipx is a tool to help you install and run end-user applications written in Python.
    It's similar to macOS's brew, JavaScript's npx, and Linux's apt.

    Benefits:
    - Installs applications into isolated environments
    - Makes applications available on your PATH
    - Safely installs packages that would conflict with system packages

    Usage after installation:
    - 'pipx install <package>' to install a Python application
    - 'pipx list' to see installed applications
    - 'pipx upgrade <package>' to upgrade an application
    """
    print_info("Setting up pipx...")

    # Install pipx via Homebrew
    install_brew_package("pipx")

    # Ensure pipx paths are properly configured
    run_command("pipx ensurepath")

    print_success("pipx installed successfully")
    print_info("You can now install Python applications with 'pipx install'")


def setup_docker_cli_colima() -> None:
    """
    Set up Docker CLI with Colima as the container runtime.

    Colima is a lightweight alternative to Docker Desktop for macOS,
    providing container runtimes with minimal setup. This configuration
    sets up Colima with:
    - 4 CPUs
    - 8GB of memory

    Benefits over Docker Desktop:
    - Lightweight and resource-efficient
    - No licensing restrictions
    - Better performance on macOS

    After installation:
    - Use 'docker' commands as normal
    - 'colima status' to check status
    - 'colima stop' to stop the runtime
    - 'colima start' to restart
    """
    print_info("Setting up Docker CLI with Colima...")

    # Install Docker CLI and related tools
    _install_docker_tools()

    # Install and configure Colima
    _setup_colima()

    print_success("Docker CLI and Colima configured (4 CPUs, 8GB memory)")


def _install_docker_tools() -> None:
    """Install Docker CLI and Docker Compose."""
    install_brew_package("docker", "formula")
    install_brew_package("docker-compose", "formula")


def _setup_colima() -> None:
    """Install and start Colima with optimized settings."""
    # Install Colima
    install_brew_package("colima", "formula")

    # Check if Colima is already running
    if _is_colima_running():
        print_success("Colima is already running")
        return

    # Start Colima with specified resources
    print_info("Starting Colima with 4 CPUs and 8GB memory...")
    run_command("colima start --cpu 4 --memory 8")


def _is_colima_running() -> bool:
    """Check if Colima is currently running."""
    colima_status = run_command("colima status", check=False)
    return colima_status is not None and "Running" in colima_status
