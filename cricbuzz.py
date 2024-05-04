import re

import requests

import constants


class Cricbuzz:
    """
    A class to fetch the live cricket scores from cricbuzz
    """

    def __init__(self) -> None:
        pass

    def fetch_current_macth_id(self) -> set:
        """
        Fetches the current avaible match ids from cricbuzz
        """
        res = requests.get("https://www.cricbuzz.com/live-cricket-scores")
        text = res.text
        pattern = r"/live-cricket-scores/(\d+)/"
        matches = re.findall(pattern, text)
        ids = set(matches)
        return ids

    def fetch_match(self, match_id: int) -> dict:
        """
        Fetches a match from cricbuzz
        """
        res = requests.get(f"{constants.CB_MATCH_BASE_URL}/{match_id}")
        data = {}
        if res.status_code == 200:
            data = res.json()
        return data

    def fetch_commentary(self, match: dict) -> list:
        """
        Fetches the commentary of a match from cricbuzz
        """
        commentary = []

        match_id = match["matchHeader"]["matchId"]
        commentary.extend(match["commentaryList"])

        self._traverse_commentary(match_id, commentary)
        return commentary

    def _traverse_commentary(self, match_id: int, commentary: list) -> None:
        """
        Traverses the commentary of a match using the timestamps
        """
        while "inningsId" in commentary[-1]:
            innings_id = commentary[-1]["inningsId"]
            time_stamp = commentary[-1]["timestamp"]
            res = requests.get(
                f"{constants.CB_COMMENTARY_PAGINATION_BASE_URL}/{match_id}/{innings_id}/{time_stamp}"
            )
            if res.status_code == 200:
                data = res.json()
                commentary.extend(data["commentaryList"])
