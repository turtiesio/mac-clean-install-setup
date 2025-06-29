#!/usr/bin/env python3
"""Core utility functions for Mac setup scripts."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


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
    description: str, lines: list[str], file_path: str = ""
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
