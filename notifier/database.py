from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from environment import Environment

env = Environment.get_instance()


class Database:
    """
    Handles all the database operations
    """

    def __init__(self):
        self.uri = env.get_mongo_uri()
        self.client = MongoClient(self.uri, server_api=ServerApi("1"))
        self.db = self.client["cricbuzz"]

    def fetch_active_match_ids(self) -> set:
        """
        Fetches the active match ids from the database
        """
        active_matches = self.db.matches.find({"matchHeader.state": "In Progress"})
        return {match["_id"] for match in active_matches}

    def fetch_commentary(self, match_id: str) -> list:
        """
        Fetches the commentary of a match from the database
        """
        commentary = self.db.commentaries.find_one({"_id": int(match_id)})
        return commentary["commentary"] if commentary else []

    def add_user_if_not_exists(self, user_id: str, match_id: str) -> dict:
        """
        Adds a user to the database if not already exists
        """
        user_exists = self.db.users.find_one({"_id": user_id})
        if user_exists is None:
            # User doesn't exist, create new user data
            notifications = {
                str(match_id): {"sentNotifications": {}, "lastNotificationSent": -1}
            }
            user_data = {
                "_id": user_id,
                "matchIds": [match_id],
                "notifications": notifications,
            }
            self.db.users.insert_one(user_data)
            return user_data

    def add_match_id_if_not_exists(self, user_id: str, match_id: str):
        """
        Adds a match ID to a user if it doesn't already exist
        """
        user_exists = self.db.users.find_one({"_id": user_id})
        if user_exists is not None and match_id not in user_exists["matchIds"]:
            # Update matchIds
            self.db.users.update_one(
                {"_id": user_id}, {"$push": {"matchIds": match_id}}
            )
            # Update notifications for the added match ID
            self.db.users.update_one(
                {"_id": user_id, f"notifications.{match_id}": {"$exists": False}},
                {
                    "$set": {
                        f"notifications.{match_id}": {
                            "sentNotifications": {},
                            "lastNotificationSent": -1,
                        }
                    }
                },
            )

    def fetch_user(self, user_id: str, match_id: str) -> dict:
        """
        Fetches user data from the database, adds user/match ID if necessary, and returns user data
        """
        user_data = self.add_user_if_not_exists(user_id, match_id)
        self.add_match_id_if_not_exists(user_id, match_id)
        return (
            user_data
            if user_data is not None
            else self.db.users.find_one({"_id": user_id})
        )

    def fetch_user_notifications(self, user_id: str, match_id: str) -> dict:
        """
        Fetches the notifications sent to the user for a specific match
        """
        user_data = self.db.users.find_one({"_id": user_id})
        if user_data and "notifications" in user_data:
            match_notifications = user_data["notifications"].get(match_id, {})
            return match_notifications.get("sentNotifications", {})
        return {}

    def update_user_notifications(
        self, user_id: str, match_id: str, notifications: dict, timestamp: int
    ) -> None:
        """
        Updates the notifications sent to the user
        """
        session = self.client.start_session()
        try:
            with session.start_transaction():
                self.db.users.update_one(
                    {"_id": user_id},
                    {
                        "$set": {
                            f"notifications.{match_id}.sentNotifications": notifications,
                            f"notifications.{match_id}.lastNotificationSent": timestamp,
                        }
                    },
                    session=session,
                )
                # Commit transaction
                session.commit_transaction()
        except Exception as e:
            session.abort_transaction()

    def close(self):
        """
        Closes the database connection
        """
        self.client.close()
