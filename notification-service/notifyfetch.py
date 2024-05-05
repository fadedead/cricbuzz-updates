from typing import AsyncGenerator, Tuple

from database import Database
from logger import Logger

mongodb = Database()


class NotificationFetcher:
    """
    Fetches the latest commentary for the match and notifies the users
    """

    def __init__(self) -> None:
        self.active_match_ids = mongodb.fetch_active_match_ids() or {}
        self.non_active_match_ids = mongodb.fetch_non_active_match_ids() or {}

    async def notify_live_fetch(
        self, user_id: str, match_id_int: int
    ) -> AsyncGenerator[Tuple[str, str], None]:
        """
        Notifies the users about the latest commentary for a specific match
        """
        match_id = str(match_id_int)
        user = mongodb.fetch_user(user_id, match_id)
        Logger.log_info(f"Fetching user data for {user_id}: {user}")

        last_notif_timestamp = user["notifications"][match_id]["lastNotificationSent"]
        commentary = await self._fetch_commentary_match(match_id, last_notif_timestamp)
        match_header = mongodb.fetch_match_header(int(match_id))
        Logger.log_info(f"Fetching commentary for {match_id}: {commentary}")

        if user["notifications"][match_id]["lastNotificationSent"] == -1:
            message = self._parse_cricket_commentary(commentary[0], match_header)
            timestamp = commentary[0]["timestamp"]
            yield message, timestamp

        for comment in reversed(commentary):
            if (
                comment["timestamp"]
                > user["notifications"][match_id]["lastNotificationSent"]
            ):
                message = self._parse_cricket_commentary(comment, match_header)
                timestamp = comment["timestamp"]
                yield message, timestamp

    async def notify_fetch_full_commentary(
        self, user_id: str, match_id_int: int
    ) -> AsyncGenerator[Tuple[str, str], None]:
        """
        Notifies the users about the latest commentary for a specific match
        """
        match_id = str(match_id_int)
        user = mongodb.fetch_user(user_id, match_id)
        Logger.log_info(f"Fetching user data for {user_id}: {user}")

        commentary = await self._fetch_commentary_match(match_id, 0)
        match_header = mongodb.fetch_match_header(int(match_id))
        Logger.log_info(f"Fetching commentary for {match_id}")

        for comment in reversed(commentary):
            message = self._parse_cricket_commentary(comment, match_header)
            timestamp = comment["timestamp"]
            yield message, timestamp

    async def _fetch_commentary_match(self, match_id: str, timestamp: int) -> list:
        """
        Fetches the latest commentary for the match
        """
        commentary = mongodb.fetch_commentary(match_id)
        commentary.sort(key=lambda x: x["timestamp"] > timestamp, reverse=True)
        return commentary

    def _parse_cricket_commentary(self, commentary: dict, match_header: dict) -> str:
        """
        Parses the cricket commentary and returns a clean string
        """
        ball_number = commentary.get("ballNbr", "")
        over_number = commentary.get("overNumber", "")
        innings = commentary.get("inningsId", "")
        batting_team = commentary.get("batTeamName", "")
        batting_score = commentary.get("batTeamScore", "")

        match_info = f"""
        Match Description: {match_header['matchDescription']}
        Match Format: {match_header['matchFormat']}
        Match Type: {match_header['matchType']}
        Series: {match_header['seriesName']}
        Game: {match_header['team1']['shortName']} vs {match_header['team2']['shortName']}
        Toss Result: {match_header['tossResults']['tossWinnerName']} won the toss and chose to {match_header['tossResults']['decision'].lower()}.
        Innings: {innings}
        Over Number: {over_number}
        Ball Number: {ball_number}
        Batting Team: {batting_team}
        Batting Score: {batting_score}
        Commentary: {commentary['commText']}
        """
        return self._format_commentary(match_info, commentary)

    def _format_commentary(self, formatted_text: str, commentary: dict) -> str:
        if (
            "commentaryFormats" in commentary
            and "bold" in commentary["commentaryFormats"]
        ):
            format_ids = commentary["commentaryFormats"]["bold"]["formatId"]
            format_values = commentary["commentaryFormats"]["bold"]["formatValue"]

            # Replace formatId with formatValue
            for i in range(len(format_ids)):
                formatted_text = formatted_text.replace(format_ids[i], format_values[i])

        return formatted_text
