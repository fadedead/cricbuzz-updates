import asyncio

import constants
from cricbuzz import Cricbuzz
from database import Database
from logger import Logger

cb = Cricbuzz()
mongodb = Database()


class Fetcher:
    """
    Fetches the data from cricbuzz and pushes it to the database
    """

    def fetch_live_matches(self) -> set:
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

    def fetch_completed_matches(self) -> set:
        """
        Fetches the ids of completed matches
        """
        completed_matches = set()

        ids = cb.fetch_current_macth_id()
        for match_id in ids:
            match = cb.fetch_match(match_id)
            match_state = match["matchHeader"]["state"] if match else None
            if match_state == "Complete":
                completed_matches.add(int(match_id))
        return completed_matches

    async def push_match_to_db(self, match_id: int) -> None:
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

    async def fetch_commentary_push_db(self, match_id: int) -> None:
        """
        Fetches the commentary and pushes it to the database
        """
        match = mongodb.check_match_exists(match_id)
        if match and not match["fullCommentaryExists"]:
            Logger.log_info(f"Fetching commentary for match {match_id}")
            commentary = cb.fetch_commentary(match)
            mongodb.update_commentary(match_id, commentary)
            Logger.log_info(f"pushed commentary for match {match_id}")

    async def fetch_completed_match_data(self) -> None:
        """
        Fetches the completed matches and pushes them to the database
        """
        while True:
            completed_matches = self.fetch_completed_matches()
            Logger.log_info(f"Completed matches: {completed_matches}")

            task_push_match_to_db = [
                self.push_match_to_db(match_id) for match_id in completed_matches
            ]

            task_push_completed_matches = [
                self.fetch_commentary_push_db(match_id)
                for match_id in completed_matches
            ]

            await asyncio.gather(*task_push_match_to_db)
            await asyncio.gather(*task_push_completed_matches)
            Logger.log_info("Completed matches pushed to db")
            await asyncio.sleep(constants.GAME_COMPLETED_FETCH_SLEEP)

    async def fetch_running_match_data(self) -> None:
        """
        Fetches the running matches and pushes them to the database
        """
        while True:
            active_matches = self.fetch_live_matches()
            Logger.log_info(f"Active Matches: {active_matches}")

            task_push_match_to_db = [
                self.push_match_to_db(match_id) for match_id in active_matches
            ]

            task_push_running_matches = [
                self.fetch_commentary_push_db(match_id) for match_id in active_matches
            ]

            await asyncio.gather(*task_push_match_to_db)
            await asyncio.gather(*task_push_running_matches)
            Logger.log_info("Active matches pushed to db")
            await asyncio.sleep(constants.GAME_UPDATE_FETCH_SLEEP)
