import asyncio
import sys
import os
from src.utils.db import get_database

# Global variable to track the running process
child_process = None


async def restart_target_script():
    """
    Terminates the old alerts_script.py process and starts a new one.
    """
    global child_process
    script_name = "alerts_script.py"

    # 1. Kill the running process if it exists
    if child_process:
        print(
            f"🔄 Restarting: Stopping current {script_name} (PID: {child_process.pid})..."
        )
        try:
            child_process.terminate()
            await child_process.wait()  # Wait for it to shut down cleanly
        except ProcessLookupError:
            pass  # Process was already dead

    # 2. Start the new process
    # sys.executable ensures we use the python form your .venv
    print(f"🚀 Starting {script_name}...")
    child_process = await asyncio.create_subprocess_exec(
        sys.executable,
        script_name,
        stdout=None,  # Inherit stdout (print to same console)
        stderr=None,  # Inherit stderr
    )


async def watch_collection():
    db = get_database()
    collection = db.WP_TICKER_ALERT

    # OPTIONAL: Start the script immediately upon running the watcher
    await restart_target_script()

    print("👀 Listening for new documents (async)...")

    # We use a debounce task to prevent restarting 100 times if 100 inserts happen at once
    debounce_task = None

    async with collection.watch() as stream:
        async for change in stream:
            op_type = change.get("operationType")

            if op_type in ["insert", "update", "delete", "replace"]:
                print(f"🔔 Detected change: {op_type}")

                # Debounce Logic:
                # If a restart is already scheduled (within the last second), cancel it
                if debounce_task:
                    debounce_task.cancel()

                # Schedule the restart to happen in 1 second
                # This groups rapid updates into a single restart
                debounce_task = asyncio.create_task(debounced_execution())


async def debounced_execution():
    """Waits for DB activity to settle before restarting."""
    try:
        await asyncio.sleep(1)  # Wait 1 second buffer
        await restart_target_script()
    except asyncio.CancelledError:
        pass  # A new change came in, so we cancelled this one to reset the timer


if __name__ == "__main__":
    try:
        asyncio.run(watch_collection())
    except KeyboardInterrupt:
        # Cleanup: Kill the child process if you stop the watcher with Ctrl+C
        if child_process:
            child_process.terminate()
        print("\nWatcher stopped.")
