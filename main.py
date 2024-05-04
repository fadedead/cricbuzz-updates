import asyncio

import aiohttp

import constants
from cricbuzz import Cricbuzz
from database import Database
from environment import Environment

cb = Cricbuzz()
mongodb = Database()
env = Environment.get_instance()


def fetch_live_and_completed_matches() -> tuple:
    """
    Fetches the ids of live and completed matches
    """
    active_matches = set()
    completed_matches = set()

    ids = cb.fetch_current_macth_id()
    for match_id in ids:
        match = cb.fetch_match(match_id)
        match_state = match["matchHeader"]["state"] if match else None
        if match_state == "In Progress":
            active_matches.add(int(match_id))
        else:
            completed_matches.add(int(match_id))
    return active_matches, completed_matches


async def push_match_to_db(match_id: int):
    """
    Pushes the match data to the database
    """
    if not mongodb.check_match_exists(match_id):
        match = cb.fetch_match(match_id)
        if not match:
            print(f"Match {match_id} not found")
            return
        mongodb.insert_match(match)
        print("Inserted match")


async def fetch_commentary_push_db(match_id: int):
    """
    Fetches the commentary and pushes it to the database
    """
    match = mongodb.check_match_exists(match_id)
    if match and not match["fullCommentaryExists"]:
        commentary = cb.fetch_commentary(match)
        mongodb.update_full_commentary(match_id, commentary)
        print(f"pushed data for match {match_id}")


async def fetch_match_data():
    """
    Fetches the active and completed matches and pushes them to the database
    """
    while True:
        active_matches, completed_matches = fetch_live_and_completed_matches()
        print("Active Matches:", active_matches)
        print("Comp Matches:", completed_matches)

        task_push_match_to_db = [
            push_match_to_db(match_id)
            for match_id in active_matches.union(completed_matches)
        ]

        task_push_completed_matches = [
            fetch_commentary_push_db(match_id) for match_id in completed_matches
        ]

        await asyncio.gather(*task_push_match_to_db)
        await asyncio.gather(*task_push_completed_matches)
        print("Sleeping")
        await asyncio.sleep(constants.GAME_LIST_FETCHER_SLEEP_TIME)


async def main():
    await fetch_match_data()


if __name__ == "__main__":
    asyncio.run(main())
