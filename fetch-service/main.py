import asyncio

import constants
from environment import Environment
from fetch import Fetcher
from logger import Logger

# Create a logger instance
Logger(constants.LOG_FILE)
Logger.log_info(f"Starting execution for fetcher service...")
Logger.log_info(f"Logger setup success for file {constants.LOG_FILE}...")

# Create Environment instances
env = Environment.get_instance()


async def main() -> None:
    """
    Runs the fetch tasks
    """
    fetcher = Fetcher()

    try:
        fetch_tasks = [
            fetcher.fetch_running_match_data(),
            fetcher.fetch_completed_match_data(),
        ]

        await asyncio.gather(*fetch_tasks)
    except Exception as e:
        Logger.log_error(f"Error in main: {e}")


if __name__ == "__main__":
    asyncio.run(main())
