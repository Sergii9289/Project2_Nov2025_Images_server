"""Development server runner with hot reload capabilities.

This script watches for changes in Python files and automatically
restarts the server when changes are detected, enabling faster
development without manual restarts.

Usage:
    python run.py

Side effects:
    - Launches a server process.
    - Monitors Python files for changes.
    - Restarts the server process when changes are detected.
    - Logs server status and error conditions.
"""

import os
import sys
import signal
import subprocess
import time
import psutil
from watchfiles import watch, Change

from settings.logging_config import get_logger

logger = get_logger(__name__)
APP_SCRIPT = os.path.join(os.path.dirname(__file__), "app.py")
WATCH_DIRS = [os.path.dirname(__file__)]


def kill_child_processes(parent_pid):
    """Terminates all child processes of the specified parent process.

    This function attempts to gracefully terminate child processes first,
    and forcefully kills any that don't respond within a timeout.

    Args:
        parent_pid (int): Process ID of the parent process.

    Side effects:
        - Terminates child processes.
        - Logs warnings if processes can't be found.
    """
    try:
        parent = psutil.Process(parent_pid)
        children = parent.children(recursive=True)

        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass

        _, alive = psutil.wait_procs(children, timeout=3)

        for child in alive:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass

    except psutil.NoSuchProcess:
        logger.warning(f"Process with PID {parent_pid} not found when trying to terminate children")


def terminate_process(process, exit_code=None):
    """Properly terminates a process and its children.

    Attempts to gracefully terminate the process first, then forcefully
    kills it if it doesn't respond within the timeout period.

    Args:
        process: The process object to terminate.
        exit_code (int, optional): If specified, exits the program with this code.

    Side effects:
        - Terminates the specified process and its children.
        - Logs warnings if process termination is not graceful.
        - Exits the program if exit_code is provided.
    """
    if not process:
        return

    kill_child_processes(process.pid)
    process.terminate()

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        logger.warning("Server process did not terminate gracefully, killing it")
        process.kill()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            logger.error("Failed to kill server process")

    if exit_code is not None:
        sys.exit(exit_code)


def run_server():
    """Starts the server process.

    Creates a subprocess running the application script and returns
    the process object.

    Returns:
        subprocess.Popen: The started server process.

    Side effects:
        - Launches a server process.
        - Logs errors if the process can't be started.
        - Exits the program on startup failure.
    """
    try:
        process = subprocess.Popen([sys.executable, APP_SCRIPT], stdout=sys.stdout, stderr=sys.stderr)
        time.sleep(1)
        return process
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error(f"Failed to start server: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point for the development server.

    Starts the server, sets up signal handlers, and monitors for file changes
    to trigger automatic server restarts.

    Side effects:
        - Sets up signal handlers for graceful shutdown.
        - Starts the server process.
        - Monitors files for changes.
        - Restarts the server when changes are detected.
        - Logs server status and errors.
    """
    logger.info("Starting development server with hot reload...")

    process = run_server()

    def signal_handler(sig, frame):
        logger.info("Shutting down server...")
        terminate_process(process, exit_code=0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        def watch_filter(change_type: Change, path: str) -> bool:
            return path.endswith(".py")

        for changes in watch(*WATCH_DIRS, watch_filter=watch_filter):
            changed_files = [path for _, path in changes]
            logger.info(f"Detected changes in: {', '.join(os.path.basename(f) for f in changed_files)}")
            logger.info("Restarting server...")

            terminate_process(process)
            time.sleep(1)

            process = run_server()
            logger.info("Server restarted successfully")

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        terminate_process(process, exit_code=0)
    except (OSError, IOError) as e:
        logger.error(f"I/O error occurred: {str(e)}")
        terminate_process(process, exit_code=1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        terminate_process(process, exit_code=1)


if __name__ == "__main__":
    main()