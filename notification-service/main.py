import asyncio
import time

import constants
from database import Database
from environment import Environment
from logger import Logger
from menu import Menu
from notify import Notifier

# Create a logger instance
log_file_name = "notification-service.log"
Logger(log_file_name)
Logger.log_info(f"Starting execution for notification service...")
Logger.log_info(f"Logger setup success for file {log_file_name}...")

# Create Database, Environment and notfication instances
mongodb = Database()
env = Environment.get_instance()
notif = Notifier()


async def fetch_commentary_match(match_id: str, timestamp: int) -> list:
    """
    Fetches the latest commentary for the match
    """
    commentary = mongodb.fetch_commentary(match_id)
    commentary.sort(key=lambda x: x["timestamp"] > timestamp, reverse=True)
    return commentary


async def notify_user(user_id: str, match_id_int: int) -> None:
    """
    Notifies the users about the latest commentary for a specific match
    """
    match_id = str(match_id_int)
    user = mongodb.fetch_user(user_id, match_id)
    Logger.log_info(f"Fetching user data for {user_id}: {user}")

    last_notif_timestamp = user["notifications"][match_id]["lastNotificationSent"]
    commentary = await fetch_commentary_match(match_id, last_notif_timestamp)
    match_header = mongodb.fetch_match_header(int(match_id))
    Logger.log_info(f"Fetching commentary for {match_id}: {commentary}")

    if user["notifications"][match_id]["lastNotificationSent"] == -1:
        message = parse_cricket_commentary(commentary[0], match_header)
        timestamp = commentary[0]["timestamp"]
        notif.notify(user_id, match_id, message, timestamp)
        return

    for comment in reversed(commentary):
        if (
            comment["timestamp"]
            > user["notifications"][match_id]["lastNotificationSent"]
        ):
            message = parse_cricket_commentary(comment, match_header)
            timestamp = comment["timestamp"]
            notif.notify(user_id, match_id, message, timestamp)


async def notify_full_commentary(user_id: str, match_id_int: int) -> None:
    """
    Notifies the users about the latest commentary for a specific match
    """
    match_id = str(match_id_int)
    user = mongodb.fetch_user(user_id, match_id)
    Logger.log_info(f"Fetching user data for {user_id}: {user}")

    commentary = await fetch_commentary_match(match_id, 0)
    match_header = mongodb.fetch_match_header(int(match_id))
    Logger.log_info(f"Fetching commentary for {match_id}")

    for comment in reversed(commentary):
        message = parse_cricket_commentary(comment, match_header)
        timestamp = comment["timestamp"]
        notif.notify(user_id, match_id, message, timestamp)
        await asyncio.sleep(1)


def parse_cricket_commentary(commentary: dict, match_header: dict) -> str:
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

    return match_info


async def main():
    """
    Main function
    """
    user = "default_user"
    mongodb.clear_match_ids(user)
    active_match_ids = mongodb.fetch_active_match_ids() or {}
    non_active_match_ids = mongodb.fetch_non_active_match_ids() or {}

    menu = Menu(active_match_ids, non_active_match_ids)
    action, match_ids = menu.menu()
    Logger.log_info(f"User action: {action} with match IDs: {match_ids}")

    if action == "PAST_MATCHES":
        for match_id in match_ids:
            await notify_full_commentary(user, match_id)
            Logger.log_info(f"Fetching commentary for matches: {match_ids}")
        print("Finished fetching commentary for past matches")
    elif action == "ACTIVE_MATCHES":
        while True:
            match_ids = mongodb.fetch_active_match_ids()
            tasks = [notify_user(user, match_id) for match_id in match_ids]
            Logger.log_info(f"Fetching commentary for matches: {match_ids}")

            await asyncio.gather(*tasks)
            await asyncio.sleep(constants.POLL_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
