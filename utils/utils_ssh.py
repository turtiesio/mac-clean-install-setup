#!/usr/bin/env python3
"""SSH-related utility functions for Mac setup scripts.

This module provides comprehensive SSH key management functionality including:
- SSH key generation with secure password generation
- SSH agent configuration with macOS keychain integration
- SSH key backup and restoration from iCloud
- Automated backup scheduling via cron
- GitHub SSH configuration and testing
"""

import os
import secrets
import string
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

from .utils_core import (
    Colors,
    command_exists,
    print_info,
    print_success,
    print_warning,
    prompt_for_user_input,
    run_command,
    setup_cron_job,
)

# Constants
SSH_KEY_TYPE = "ed25519"
SSH_KEY_FILENAME = f"id_{SSH_KEY_TYPE}"
SSH_CONFIG_MARKER = "# Configured by mac-setup"
BACKUP_DIR_PATH = "Library/Mobile Documents/com~apple~CloudDocs/Backup/ssh"
BACKUP_RETENTION_COUNT = 4
PASSWORD_LENGTH = 32


def _create_askpass_script(password: str) -> Path:
    """Create a temporary askpass script for SSH key operations.

    Args:
        password: The password to embed in the askpass script

    Returns:
        Path to the created askpass script

    Note:
        The caller is responsible for cleaning up the created file.
    """
    askpass_content = f"""#!/bin/bash
echo '{password}'
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as tmp_file:
        tmp_file.write(askpass_content)
        askpass_path = Path(tmp_file.name)

    # Make the script executable
    askpass_path.chmod(0o700)
    return askpass_path


def _add_key_to_agent_with_password(key_path: Path, password: str) -> bool:
    """Add SSH key to agent using SSH_ASKPASS mechanism for password-protected keys.

    Args:
        key_path: Path to the SSH private key
        password: Password for the SSH key

    Returns:
        True if the key was successfully added, False otherwise
    """
    askpass_path = _create_askpass_script(password)

    try:
        # Configure environment for SSH_ASKPASS
        env = os.environ.copy()
        env.update(
            {
                "DISPLAY": "1",  # Required for SSH_ASKPASS to work
                "SSH_ASKPASS": str(askpass_path),
                "SSH_ASKPASS_REQUIRE": "force",
            }
        )

        # Add key to agent with macOS keychain support
        result = subprocess.run(
            ["ssh-add", "--apple-use-keychain", str(key_path)],
            env=env,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    finally:
        # Clean up the temporary askpass script
        askpass_path.unlink(missing_ok=True)


def _get_ssh_key_fingerprint(key_path: Path) -> Optional[str]:
    """Extract the fingerprint from an SSH key file.

    Args:
        key_path: Path to the SSH key file

    Returns:
        The fingerprint string if successful, None otherwise
    """
    output = run_command(f"ssh-keygen -lf {key_path}", check=False)
    if output and len(output.split()) > 1:
        return output.split()[1]
    return None


def _is_key_in_agent(key_path: Path) -> bool:
    """Check if an SSH key is already loaded in the SSH agent.

    Args:
        key_path: Path to the SSH key to check

    Returns:
        True if the key is already in the agent, False otherwise
    """
    agent_keys = run_command("ssh-add -l", check=False)
    if not agent_keys:
        return False

    key_fingerprint = _get_ssh_key_fingerprint(key_path)
    return key_fingerprint and key_fingerprint in agent_keys


def _key_has_passphrase(key_path: Path) -> bool:
    """Check if an SSH key is protected by a passphrase.

    Args:
        key_path: Path to the SSH key file

    Returns:
        True if the key has a passphrase, False otherwise
    """
    result = subprocess.run(
        ["ssh-keygen", "-y", "-f", str(key_path)], capture_output=True, text=True
    )
    return result.returncode != 0


def _setup_ssh_config(ssh_dir: Path) -> None:
    """Setup SSH config for GitHub and general usage with macOS keychain integration.

    Args:
        ssh_dir: Path to the .ssh directory
    """
    config_file = ssh_dir / "config"

    # SSH configuration with best practices for macOS
    ssh_config = f"""{SSH_CONFIG_MARKER}
Host *
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/{SSH_KEY_FILENAME}
  ServerAliveInterval 60
  ServerAliveCountMax 3
"""

    if config_file.exists():
        existing_config = config_file.read_text()

        # Check if we've already configured this file
        if SSH_CONFIG_MARKER not in existing_config:
            # Ensure proper line ending before appending
            if existing_config and not existing_config.endswith("\n"):
                existing_config += "\n"

            config_file.write_text(existing_config + "\n" + ssh_config)
            print_info("Added SSH config to existing file")
        else:
            print_info("SSH config already configured by mac-setup")
    else:
        config_file.write_text(ssh_config)
        print_info("Created new SSH config")

    # Ensure secure permissions
    config_file.chmod(0o600)


def _add_existing_key_to_agent(key_path: Path) -> None:
    """Add an existing SSH key to ssh-agent, prompting for password if needed.

    Args:
        key_path: Path to the SSH key to add
    """
    # Start ssh-agent if needed
    run_command('eval "$(ssh-agent -s)"', check=False)

    # Check if key is already in agent
    if _is_key_in_agent(key_path):
        print_success(f"{key_path.name} is already in ssh-agent")
        return

    print_info(f"Adding {key_path.name} to ssh-agent...")

    if _key_has_passphrase(key_path):
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
                f"Could not add {key_path.name} to ssh-agent. "
                "You may need to add it manually."
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


def _find_ssh_backups() -> List[Path]:
    """Find SSH backup files in iCloud backup directory.

    Returns:
        List of backup file paths, sorted by most recent first
    """
    backup_dir = Path(os.environ["HOME"]) / BACKUP_DIR_PATH
    if not backup_dir.exists():
        return []

    return sorted(backup_dir.glob("ssh_backup_*.zip"), reverse=True)


def _restore_ssh_from_backup(backup_path: Path, ssh_dir: Path) -> None:
    """Restore SSH keys from a backup zip file.

    Args:
        backup_path: Path to the backup zip file
        ssh_dir: Path to the .ssh directory
    """
    print_info("Restoring SSH keys from backup...")

    # Extract backup to home directory
    with zipfile.ZipFile(backup_path, "r") as zip_ref:
        zip_ref.extractall(os.environ["HOME"])

    # Fix directory and file permissions
    ssh_dir.chmod(0o700)
    for file_path in ssh_dir.iterdir():
        if file_path.name.startswith("id_"):
            if file_path.name.endswith(".pub"):
                file_path.chmod(0o644)  # Public keys are readable
            else:
                file_path.chmod(0o600)  # Private keys are restricted

    print_success("SSH keys restored from backup")

    # Add all restored keys to ssh-agent
    for key_file in ssh_dir.glob("id_*"):
        if not key_file.name.endswith(".pub"):
            _add_existing_key_to_agent(key_file)


def _generate_secure_password() -> str:
    """Generate a cryptographically secure random password.

    Returns:
        A secure random password string
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(alphabet) for _ in range(PASSWORD_LENGTH))


def _display_password_warning(password: str) -> None:
    """Display a prominent warning about saving the SSH key password.

    Args:
        password: The generated password to display
    """
    separator = "=" * 60

    print("\n" + separator)
    print(f"{Colors.YELLOW}⚠️  IMPORTANT: SAVE THIS PASSWORD ⚠️{Colors.RESET}")
    print(separator)
    print(f"\n{Colors.BLUE}Generated secure SSH key password:{Colors.RESET}")
    print(f"\n{Colors.GREEN}{password}{Colors.RESET}\n")
    print(
        f"{Colors.YELLOW}Please save this password in your password manager NOW!{Colors.RESET}"
    )
    print("You will need it when using this SSH key.")
    print(separator + "\n")


def _generate_ssh_key(email: str, key_path: Path, password: str) -> None:
    """Generate a new SSH key with the specified parameters.

    Args:
        email: Email address to associate with the key
        key_path: Path where the key should be created
        password: Password to protect the key
    """
    print_info(f"Generating {SSH_KEY_TYPE.upper()} SSH key...")

    # Generate key without passphrase initially
    subprocess.run(
        ["ssh-keygen", "-t", SSH_KEY_TYPE, "-C", email, "-f", str(key_path), "-N", ""],
        check=True,
    )

    # Add passphrase to the key
    print_info("Adding passphrase to SSH key...")
    subprocess.run(
        ["ssh-keygen", "-p", "-f", str(key_path), "-N", password, "-P", ""],
        check=True,
        capture_output=True,
    )


def _display_public_key(key_path: Path) -> None:
    """Display the public key and copy it to clipboard if possible.

    Args:
        key_path: Path to the private key (public key path will be derived)
    """
    public_key_path = f"{key_path}.pub"
    public_key = run_command(f"cat {public_key_path}")

    separator = "=" * 60
    print("\n" + separator)
    print(f"{Colors.GREEN}✓ SSH key generated successfully!{Colors.RESET}")
    print(separator)
    print(f"\n{Colors.BLUE}Your SSH public key:{Colors.RESET}\n")
    print(public_key)

    # Copy to clipboard if pbcopy is available
    if command_exists("pbcopy"):
        run_command(f"cat {public_key_path} | pbcopy")
        print(f"\n{Colors.GREEN}✓ Public key copied to clipboard!{Colors.RESET}")


def _display_github_instructions() -> None:
    """Display instructions for adding SSH key to GitHub."""
    separator = "=" * 60

    print("\n" + separator)
    print(f"{Colors.YELLOW}⚠️  MANUAL CONFIGURATION REQUIRED ⚠️{Colors.RESET}")
    print(separator)
    print(f"\n{Colors.BLUE}Add your SSH key to GitHub:{Colors.RESET}")
    print("  1. The public key has been copied to your clipboard")
    print("  2. Open GitHub SSH settings: https://github.com/settings/keys")
    print("  3. Click 'New SSH key'")
    print("  4. Give it a title (e.g., 'MacBook Pro')")
    print("  5. Paste the key and click 'Add SSH key'")
    print("\n  Note: The key is already added to your SSH agent with keychain.")
    print(separator + "\n")


def _test_github_connection(ssh_dir: Path) -> None:
    """Test SSH connection to GitHub and add to known hosts if needed.

    Args:
        ssh_dir: Path to the .ssh directory
    """
    print_info("Testing SSH connection to GitHub...")

    # Add GitHub to known hosts if not already there
    known_hosts_file = ssh_dir / "known_hosts"
    if (
        not known_hosts_file.exists()
        or "github.com" not in known_hosts_file.read_text()
    ):
        print_info("Adding GitHub to known hosts...")
        run_command(
            f"ssh-keyscan -t {SSH_KEY_TYPE} github.com >> ~/.ssh/known_hosts",
            check=False,
        )

    # Test the connection
    test_result = run_command("ssh -T git@github.com 2>&1", check=False)
    if test_result and "successfully authenticated" in test_result:
        print_success("GitHub SSH authentication successful!")
    else:
        print_warning("Could not verify GitHub connection.")
        print_info("Try running manually: ssh -T git@github.com")


def setup_ssh_key() -> None:
    """Generate a new SSH key with secure password and configure ssh-agent.

    This function handles the complete SSH key setup process including:
    - Checking for existing keys
    - Offering to restore from backup
    - Generating new keys with secure passwords
    - Configuring SSH agent and config
    - Setting up GitHub integration
    """
    print_info("Setting up SSH key...")

    # Ensure SSH directory exists with proper permissions
    ssh_dir = Path(os.environ["HOME"]) / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)

    # Check if default key already exists
    key_path = ssh_dir / SSH_KEY_FILENAME
    if key_path.exists():
        print_success(f"SSH key already exists at ~/.ssh/{SSH_KEY_FILENAME}")
        _add_existing_key_to_agent(key_path)
        return

    # Check for SSH backups in iCloud
    backups = _find_ssh_backups()
    if backups:
        print_info(f"Found {len(backups)} SSH backup(s) in iCloud")
        print(f"\n{Colors.BLUE}Most recent backup:{Colors.RESET} {backups[0].name}")

        response = input(
            f"{Colors.YELLOW}Would you like to restore from backup? (yes/no): {Colors.RESET}"
        ).lower()

        if response == "yes":
            _restore_ssh_from_backup(backups[0], ssh_dir)
            return

    # Generate new SSH key
    password = _generate_secure_password()
    _display_password_warning(password)
    prompt_for_user_input(
        "Type 'saved' when you have saved this password", expected_response="saved"
    )

    # Get user email
    email = input(
        f"{Colors.BLUE}Enter your email address for the SSH key "
        f"(used for Git commits): {Colors.RESET}"
    )

    # Generate the SSH key
    _generate_ssh_key(email, key_path, password)

    # Configure SSH
    _setup_ssh_config(ssh_dir)

    # Add key to ssh-agent
    print_info("Adding SSH key to ssh-agent...")
    run_command('eval "$(ssh-agent -s)"')

    if _add_key_to_agent_with_password(key_path, password):
        print_success("SSH key added to ssh-agent with keychain")
    else:
        print_warning("Failed to add SSH key to agent")

    # Display public key and GitHub instructions
    _display_public_key(key_path)
    _display_github_instructions()

    prompt_for_user_input(
        "Type 'done' when you have added the key to GitHub", expected_response="done"
    )

    # Test GitHub connection
    _test_github_connection(ssh_dir)

    print_success("SSH key setup completed")


def _create_backup_script(backup_dir: str) -> str:
    """Create the SSH backup shell script content.

    Args:
        backup_dir: Directory where backups should be stored

    Returns:
        The backup script content
    """
    return f"""#!/bin/bash
# SSH Backup Script - Automatically backs up SSH keys to iCloud

# Configuration
BACKUP_DIR="{backup_dir}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ZIP_FILE="$BACKUP_DIR/ssh_backup_$TIMESTAMP.zip"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create zip backup of .ssh directory
cd "$HOME" && zip -r "$ZIP_FILE" .ssh/

# Keep only the {BACKUP_RETENTION_COUNT} most recent backups
cd "$BACKUP_DIR" && ls -t ssh_backup_*.zip | tail -n +{BACKUP_RETENTION_COUNT + 1} | xargs -r rm

echo "SSH backup completed: $ZIP_FILE"
"""


def setup_ssh_backup_cron() -> None:
    """Setup weekly cron job to backup SSH keys to iCloud.

    Creates a backup script and schedules it to run weekly on Sundays at 2 AM.
    Backups are stored in iCloud Drive with automatic rotation.
    """
    print_info("Setting up SSH backup cron job...")

    # Prepare paths
    home = os.environ["HOME"]
    backup_dir = f"{home}/{BACKUP_DIR_PATH}"
    scripts_dir = Path(home) / ".local" / "bin"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    # Create backup script
    script_path = scripts_dir / "ssh_backup.sh"
    backup_script = _create_backup_script(backup_dir)
    script_path.write_text(backup_script)
    script_path.chmod(0o755)

    # Setup cron job to run weekly on Sunday at 2 AM
    setup_cron_job(
        "0 2 * * 0",  # Cron expression for weekly on Sunday at 2 AM
        str(script_path),
        "Weekly SSH backup to iCloud",
    )

    print_success("SSH backup cron job configured (weekly on Sundays at 2 AM)")
    print_info(f"Backup script created at: {script_path}")
    print_info(f"Backups will be saved to: {backup_dir}")
