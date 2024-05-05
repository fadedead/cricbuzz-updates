import asyncio

import constants
from cricbuzz import Cricbuzz
from database import Database
from environment import Environment
from logger import Logger

# Create a logger instance
log_file_name = "fetcher-service.log"
Logger(log_file_name)
Logger.log_info(f"Starting execution for fetcher service...")
Logger.log_info(f"Logger setup success for file {log_file_name}...")

# Create Cricbuzz, Database and Environment instances
cb = Cricbuzz()
mongodb = Database()
env = Environment.get_instance()


def fetch_live_matches() -> set:
    """
    Fetches the ids of live matches
    """
    active_matches = set()

    ids = cb.fetch_current_macth_id()
    for match_id in ids:
        match = cb.fetch_match(match_id)
        match_state = match["matchHeader"]["state"] if match else None
        if match_state == "In Progress":
            active_matches.add(int(match_id))
    return active_matches


def fetch_completed_matches() -> set:
    """
    Fetches the ids of completed matches
    """
    completed_matches = set()

    ids = cb.fetch_current_macth_id()
    for match_id in ids:
        match = cb.fetch_match(match_id)
        match_state = match["matchHeader"]["state"] if match else None
        if match_state != "In Progress":
            completed_matches.add(int(match_id))
    return completed_matches


async def push_match_to_db(match_id: int):
    """
    Pushes the match data to the database
    """
    Logger.log_info(f"Fetching data for match {match_id}")
    match = cb.fetch_match(match_id)
    if not match:
        Logger.log_info(f"The match ID has no data yet: {match_id}")
        return
    mongodb.upsert_match(match)
    Logger.log_info(f"pushed data for match {match_id}")


async def fetch_commentary_push_db(match_id: int):
    """
    Fetches the commentary and pushes it to the database
    """
    match = mongodb.check_match_exists(match_id)
    if match and not match["fullCommentaryExists"]:
        Logger.log_info(f"Fetching commentary for match {match_id}")
        commentary = cb.fetch_commentary(match)
        mongodb.update_commentary(match_id, commentary)
        Logger.log_info(f"pushed commentary for match {match_id}")


async def fetch_completed_match_data():
    """
    Fetches the completed matches and pushes them to the database
    """
    while True:
        completed_matches = fetch_completed_matches()
        Logger.log_info(f"Completed matches: {completed_matches}")

        task_push_match_to_db = [
            push_match_to_db(match_id) for match_id in completed_matches
        ]

        task_push_completed_matches = [
            fetch_commentary_push_db(match_id) for match_id in completed_matches
        ]

        await asyncio.gather(*task_push_match_to_db)
        await asyncio.gather(*task_push_completed_matches)
        Logger.log_info("Completed matches pushed to db")
        await asyncio.sleep(constants.GAME_COMPLETED_FETCH_SLEEP)


async def fetch_running_match_data():
    """
    Fetches the running matches and pushes them to the database
    """
    while True:
        active_matches = fetch_live_matches()
        Logger.log_info(f"Active Matches: {active_matches}")

        task_push_match_to_db = [
            push_match_to_db(match_id) for match_id in active_matches
        ]

        task_push_running_matches = [
            fetch_commentary_push_db(match_id) for match_id in active_matches
        ]

        await asyncio.gather(*task_push_match_to_db)
        await asyncio.gather(*task_push_running_matches)
        Logger.log_info("Active matches pushed to db")
        await asyncio.sleep(constants.GAME_UPDATE_FETCH_SLEEP)


async def main():
    """
    Runs the fetch tasks
    """
    try:
        fetch_tasks = [
            fetch_running_match_data(),
            fetch_completed_match_data(),
        ]

        await asyncio.gather(*fetch_tasks)
    except Exception as e:
        Logger.log_error(f"Error in main: {e}")
        raise e


if __name__ == "__main__":
    asyncio.run(main())
