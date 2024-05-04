import asyncio

import constants
from database import Database
from environment import Environment
from notify import Notifier

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

    last_notif_timestamp = user["notifications"][match_id]["lastNotificationSent"]
    commentary = await fetch_commentary_match(match_id, last_notif_timestamp)

    if user["notifications"][match_id]["lastNotificationSent"] == -1:
        message = commentary[0]["commText"]
        timestamp = commentary[0]["timestamp"]
        notif.notify(user_id, match_id, message, timestamp)
        return

    for comment in reversed(commentary):
        if (
            comment["timestamp"]
            > user["notifications"][match_id]["lastNotificationSent"]
        ):
            message = f"{comment['commText']}"
            timestamp = comment["timestamp"]
            notif.notify(user_id, match_id, message, timestamp)


async def main():
    """
    Main function
    """
    while True:
        match_ids = mongodb.fetch_active_match_ids()
        tasks = [notify_user("default_user", match_id) for match_id in match_ids]
        await asyncio.gather(*tasks)
        await asyncio.sleep(constants.POLL_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
