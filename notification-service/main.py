import asyncio
import time

import constants
from environment import Environment
from logger import Logger
from menu import Menu
from notifyfetch import NotificationFetcher
from notifysend import NotificationSender

# Create a logger instance
Logger(constants.LOG_FILE)
Logger.log_info(f"Starting execution for notification service...")
Logger.log_info(f"Logger setup success for file {constants.LOG_FILE}...")

# Create Environment instances
env = Environment.get_instance()


async def main() -> None:
    """
    Main function
    """
    user = "default_user"
    notif_fetch = NotificationFetcher()
    notif_send = NotificationSender()

    notif_send.clear_all_sent_notifications(user)

    menu = Menu(notif_fetch.active_match_ids, notif_fetch.non_active_match_ids)
    action, match_ids = menu.menu()
    Logger.log_info(f"User action: {action} with match IDs: {match_ids}")

    if action == "NON_ACTIVE_MATCHES":

        for match_id in match_ids:
            async for (
                message,
                timestamp,
            ) in notif_fetch.notify_fetch_full_commentary(user, match_id):
                notif_send.notify(user, match_id, message, timestamp)
                await asyncio.sleep(1)
            Logger.log_info(f"Fetching commentary for matches: {match_ids}")
        print("Finished fetching commentary for past matches")
    elif action == "ACTIVE_MATCHES":
        while True:
            Logger.log_info(f"Fetching commentary for matches: {match_ids}")
            for match_id in match_ids:
                async for (
                    message,
                    timestamp,
                ) in notif_fetch.notify_live_fetch(user, match_id):
                    notif_send.notify(user, match_id, message, timestamp)

            await asyncio.sleep(constants.POLL_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
