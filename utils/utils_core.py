#!/usr/bin/env python3
"""Core utility functions for Mac setup scripts.

This module provides essential utilities for system configuration, including:
- Colored console output for better UX
- Command execution with error handling
- Configuration file management
- Cron job and LaunchAgent setup
- Progress tracking for multi-step processes
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

# ===== ANSI Color Codes =====


class Colors:
    """ANSI color codes for terminal output formatting.

    Provides a clean interface for colored console output to improve
    readability and user experience during script execution.
    """

    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


# ===== Console Output Functions =====


def print_success(message: str) -> None:
    """Print a success message with a green checkmark.

    Args:
        message: The success message to display
    """
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def print_error(message: str) -> None:
    """Print an error message with a red X mark.

    Args:
        message: The error message to display
    """
    print(f"{Colors.RED}✗{Colors.RESET} {message}")


def print_info(message: str) -> None:
    """Print an informational message with a blue arrow.

    Args:
        message: The info message to display
    """
    print(f"{Colors.BLUE}→{Colors.RESET} {message}")


def print_warning(message: str) -> None:
    """Print a warning message with a yellow exclamation mark.

    Args:
        message: The warning message to display
    """
    print(f"{Colors.YELLOW}!{Colors.RESET} {message}")


# ===== Command Execution =====


def run_command(
    command: str, check: bool = True, shell: str = "/bin/zsh"
) -> Optional[str]:
    """Execute a shell command and return its output.

    Args:
        command: The shell command to execute
        check: If True, raise CalledProcessError on non-zero exit
        shell: Path to the shell executable (defaults to zsh)

    Returns:
        The command's stdout as a string if successful, None if failed

    Raises:
        subprocess.CalledProcessError: If check=True and command fails
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True,
            executable=shell,
        )

        if result.returncode == 0:
            return result.stdout.strip()
        return None

    except subprocess.CalledProcessError:
        if check:
            raise
        return None


def command_exists(command_name: str) -> bool:
    """Check if a command is available in the system PATH.

    Args:
        command_name: Name of the command to check

    Returns:
        True if the command exists, False otherwise
    """
    result = run_command(f"which {command_name}", check=False)
    return result is not None and result != ""


# ===== Progress Tracking =====


def get_completion_flag_path(flag_name: str) -> Path:
    """Get the path for a completion flag file.

    Flag files are used to track which steps of a multi-stage setup
    process have been completed, allowing scripts to resume from
    interruptions.

    Args:
        flag_name: Unique identifier for the completion flag

    Returns:
        Path object pointing to the flag file location
    """
    flags_directory = Path(tempfile.gettempdir()) / "mac-setup-flags"
    flags_directory.mkdir(exist_ok=True)
    return flags_directory / f"{flag_name}.completed"


def is_step_completed(flag_name: str) -> bool:
    """Check if a setup step has been marked as completed.

    Args:
        flag_name: Unique identifier for the step

    Returns:
        True if the step is marked as completed, False otherwise
    """
    flag_path = get_completion_flag_path(flag_name)
    return flag_path.exists()


def mark_step_completed(flag_name: str) -> None:
    """Mark a setup step as completed by creating its flag file.

    Args:
        flag_name: Unique identifier for the step
    """
    flag_path = get_completion_flag_path(flag_name)
    flag_path.touch()
    print_success(f"Marked {flag_name} as completed")


# ===== Shell Configuration Management =====


def cleanup_auto_generated_blocks(config_file_path: str = "") -> None:
    """Remove all auto-generated configuration blocks from a shell config file.

    This function removes any content between START and END markers that were
    previously added by our setup scripts, while preserving user additions.

    Args:
        config_file_path: Path to the config file (defaults to ~/.zshrc)
    """
    config_path = Path(config_file_path or f"{os.environ['HOME']}/.zshrc")

    if not config_path.exists():
        return

    # Read and process the file line by line
    lines = config_path.read_text().splitlines()
    cleaned_lines = _remove_auto_generated_sections(lines)
    consolidated_lines = _remove_consecutive_empty_lines(cleaned_lines)

    # Write back the cleaned content
    config_path.write_text("\n".join(consolidated_lines) + "\n")
    print_success(f"Cleaned up auto-generated blocks from {config_path}")


def _remove_auto_generated_sections(lines: List[str]) -> List[str]:
    """Remove lines between auto-generated markers.

    Args:
        lines: List of file lines

    Returns:
        List of lines with auto-generated sections removed
    """
    cleaned_lines = []
    inside_auto_section = False

    for line in lines:
        if "###### START(AUTO-GENERATED DO NOT EDIT) ######" in line:
            inside_auto_section = True
        elif "###### END(AUTO-GENERATED DO NOT EDIT) ######" in line:
            inside_auto_section = False
        elif not inside_auto_section:
            cleaned_lines.append(line)

    return cleaned_lines


def _remove_consecutive_empty_lines(lines: List[str]) -> List[str]:
    """Remove consecutive empty lines, keeping at most one.

    Args:
        lines: List of file lines

    Returns:
        List of lines with consecutive empty lines removed
    """
    consolidated = []

    for i, line in enumerate(lines):
        # Keep the line if it's not empty OR if it's the first line OR
        # if the previous line wasn't empty
        if line or i == 0 or (i > 0 and lines[i - 1]):
            consolidated.append(line)

    return consolidated


def append_shell_section(
    description: str, config_lines: List[str], config_file_path: str = ""
) -> None:
    """Append a configuration section with protective markers to shell config.

    This function adds configuration lines wrapped in special markers that
    identify them as auto-generated content. This allows for safe cleanup
    and updates without affecting user customizations.

    Args:
        description: Human-readable description of the section
        config_lines: List of configuration lines to add
        config_file_path: Path to the config file (defaults to ~/.zshrc)
    """
    config_path = Path(config_file_path or f"{os.environ['HOME']}/.zshrc")

    # Create markers for this section
    start_marker = f"# {description} ###### START(AUTO-GENERATED DO NOT EDIT) ######"
    end_marker = f"# {description} ###### END(AUTO-GENERATED DO NOT EDIT) ######"

    # Read existing content
    content = config_path.read_text() if config_path.exists() else ""

    # Ensure proper spacing before new section
    content = _ensure_trailing_newlines(content, count=2)

    # Add the new section
    content += start_marker + "\n"
    content += "\n".join(config_lines) + "\n"
    content += end_marker + "\n"

    config_path.write_text(content)
    print_success(f"Added section to {config_path}: {description}")


def _ensure_trailing_newlines(content: str, count: int) -> str:
    """Ensure content ends with the specified number of newlines.

    Args:
        content: The text content to process
        count: Desired number of trailing newlines

    Returns:
        Content with the correct number of trailing newlines
    """
    if not content:
        return ""

    # Strip all trailing newlines and add the desired amount
    content = content.rstrip("\n")
    return content + "\n" * count


# ===== Cron Job Management =====


def clear_crontab() -> bool:
    """Clear all cron jobs for the current user.

    This function safely removes all cron jobs. It checks if a crontab
    exists before attempting to clear it.

    Returns:
        True if crontab was cleared successfully, False otherwise
    """
    print_info("Clearing crontab...")

    # Check if there's an existing crontab
    existing_crontab = run_command("crontab -l 2>/dev/null", check=False)

    if not existing_crontab:
        print_success("Crontab is already empty")
        return True

    # Clear the crontab
    clear_result = run_command("crontab -r 2>/dev/null", check=False)

    # Verify it was cleared
    verification = run_command("crontab -l 2>/dev/null", check=False)

    if clear_result is not None or verification is None:
        print_success("Crontab cleared successfully")
        return True
    else:
        print_error("Failed to clear crontab")
        return False


def setup_cron_job(
    schedule: str, command: str, description: str = "", check_exists: bool = True
) -> bool:
    """Setup a cron job with the specified schedule and command.

    This function adds a new cron job to the user's crontab. It can optionally
    check for duplicates and add descriptive comments.

    Args:
        schedule: Cron schedule expression (e.g., "0 9 * * *" for daily at 9am)
        command: Command to execute
        description: Optional description comment for the cron job
        check_exists: If True, skip adding if similar job already exists

    Returns:
        True if cron job was added successfully, False otherwise

    Example:
        >>> setup_cron_job(
        ...     "0 9 * * *",
        ...     "/usr/bin/python3 /path/to/backup.py",
        ...     "Daily backup at 9am"
        ... )
    """
    print_info(f"Setting up cron job: {description or command}")

    # Get current crontab
    current_crontab = run_command("crontab -l 2>/dev/null", check=False) or ""

    # Check if job already exists
    if check_exists and command in current_crontab:
        print_success("Cron job already exists")
        return True

    # Prepare new cron entry
    cron_entry = _format_cron_entry(schedule, command, description)

    # Update crontab
    success = _update_crontab(current_crontab, cron_entry)

    if success:
        print_success(f"Cron job added: {schedule} {command}")
    else:
        print_error("Failed to install cron job")

    return success


def _format_cron_entry(schedule: str, command: str, description: str) -> str:
    """Format a cron entry with optional description comment.

    Args:
        schedule: Cron schedule expression
        command: Command to execute
        description: Optional description

    Returns:
        Formatted cron entry as a string
    """
    entry = ""
    if description:
        entry += f"# {description}\n"
    entry += f"{schedule} {command}\n"
    return entry


def _update_crontab(current_content: str, new_entry: str) -> bool:
    """Update the crontab with new content.

    Args:
        current_content: Existing crontab content
        new_entry: New cron entry to add

    Returns:
        True if update was successful, False otherwise
    """
    # Create temporary file with updated crontab
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
        # Ensure current content ends with newline
        if current_content and not current_content.endswith("\n"):
            current_content += "\n"

        tmp_file.write(current_content)
        tmp_file.write(new_entry)
        tmp_path = tmp_file.name

    try:
        # Install new crontab
        result = run_command(f"crontab {tmp_path}", check=False)
        return result is not None
    finally:
        # Clean up temporary file
        Path(tmp_path).unlink(missing_ok=True)


# ===== LaunchAgent Management =====


def create_launch_agent(agent_name: str, plist_content: str) -> None:
    """Create a macOS LaunchAgent plist file.

    LaunchAgents are macOS's preferred way to run background tasks and
    scheduled jobs. This function creates a properly formatted plist file
    in the user's LaunchAgents directory.

    Args:
        agent_name: Reverse-DNS style name (e.g., 'com.example.MyAgent')
        plist_content: The XML content of the plist file

    Example:
        >>> plist = '''<?xml version="1.0" encoding="UTF-8"?>
        ... <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
        ...   "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        ... <plist version="1.0">
        ... <dict>
        ...     <key>Label</key>
        ...     <string>com.example.backup</string>
        ...     <key>ProgramArguments</key>
        ...     <array>
        ...         <string>/usr/bin/python3</string>
        ...         <string>/path/to/backup.py</string>
        ...     </array>
        ...     <key>StartCalendarInterval</key>
        ...     <dict>
        ...         <key>Hour</key>
        ...         <integer>9</integer>
        ...         <key>Minute</key>
        ...         <integer>0</integer>
        ...     </dict>
        ... </dict>
        ... </plist>'''
        >>> create_launch_agent("com.example.backup", plist)
    """
    # Ensure LaunchAgents directory exists
    launch_agents_dir = Path(f"{os.environ['HOME']}/Library/LaunchAgents")
    launch_agents_dir.mkdir(parents=True, exist_ok=True)

    # Write the plist file
    plist_path = launch_agents_dir / f"{agent_name}.plist"
    plist_path.write_text(plist_content)

    print_success(f"Created LaunchAgent: {plist_path}")


# ===== User Input Utilities =====


def prompt_for_user_input(
    message: str,
    valid_responses: Optional[List[str]] = None,
    expected_response: Optional[str] = None,
    case_sensitive: bool = False,
) -> str:
    """Prompt user for input with optional validation.

    This is a unified function that handles various types of user prompts:
    - Free-form input (when no validation specified)
    - Multiple choice (when valid_responses provided)
    - Specific confirmation (when expected_response provided)

    Args:
        message: The prompt message to display
        valid_responses: Optional list of valid responses
        expected_response: Optional single expected response
        case_sensitive: Whether to treat responses as case-sensitive

    Returns:
        The user's response (lowercase by default unless case_sensitive=True)

    Examples:
        >>> # Multiple choice prompt
        >>> response = prompt_for_user_input(
        ...     "Continue with installation?",
        ...     valid_responses=["yes", "no", "skip"]
        ... )

        >>> # Specific confirmation
        >>> prompt_for_user_input(
        ...     "Type 'DELETE' to confirm deletion",
        ...     expected_response="DELETE",
        ...     case_sensitive=True
        ... )

        >>> # Free-form input
        >>> name = prompt_for_user_input("Enter your name")
    """
    # Initial prompt
    response = input(f"{Colors.YELLOW}{message}: {Colors.RESET}")

    # Normalize case if not case-sensitive
    if not case_sensitive:
        response = response.lower()
        if valid_responses:
            valid_responses = [r.lower() for r in valid_responses]
        if expected_response:
            expected_response = expected_response.lower()

    # Validation loop
    while True:
        # Check for expected single response
        if expected_response and response != expected_response:
            response = input(
                f"{Colors.YELLOW}Please type '{expected_response}' to confirm: {Colors.RESET}"
            )
            if not case_sensitive:
                response = response.lower()

        # Check for valid responses list
        elif valid_responses and response not in valid_responses:
            valid_options = "' or '".join(valid_responses)
            response = input(
                f"{Colors.YELLOW}Please type '{valid_options}' to continue: {Colors.RESET}"
            )
            if not case_sensitive:
                response = response.lower()

        # No validation needed or validation passed
        else:
            break

    return response
