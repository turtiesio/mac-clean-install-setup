#!/usr/bin/env python3
"""SSH-related utility functions for Mac setup scripts."""

import os
import subprocess
import tempfile
from pathlib import Path

from utils_core import (
    Colors,
    command_exists,
    print_info,
    print_success,
    print_warning,
    run_command,
    setup_cron_job,
)


def _add_key_to_agent_with_password(key_path: Path, password: str) -> bool:
    """Add SSH key to agent using SSH_ASKPASS mechanism."""
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
