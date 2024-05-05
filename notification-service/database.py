from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from environment import Environment
from logger import Logger

env = Environment.get_instance()


class Database:
    """
    Handles all the database operations
    """

    def __init__(self):
        try:
            self.uri = env.get_mongo_uri()
            self.client = MongoClient(self.uri, server_api=ServerApi("1"))
            self.db = self.client["cricbuzz"]
        except Exception as e:
            Logger.log_error(f"Error connecting to MongoDB: {e}")
            raise e

    def fetch_active_match_ids(self) -> set:
        """
        Fetches the active match ids from the database
        """
        try:
            active_matches = self.db.matches.find({"matchHeader.state": "In Progress"})
            return {match["_id"] for match in active_matches}
        except Exception as e:
            Logger.log_error(f"Error fetching active match IDs: {e}")
            raise e

    def fetch_non_active_match_ids(self) -> set:
        """
        Fetches the non-active match ids from the database
        """
        try:
            non_active_matches = self.db.matches.find(
                {"matchHeader.state": {"$ne": "In Progress"}}
            )
            return {match["_id"] for match in non_active_matches}
        except Exception as e:
            Logger.log_error(f"Error fetching non-active match IDs: {e}")
            raise e

    def fetch_commentary(self, match_id: str) -> list:
        """
        Fetches the commentary of a match from the database
        """
        try:
            commentary = self.db.commentaries.find_one({"_id": int(match_id)})
            return commentary["commentary"] if commentary else []
        except Exception as e:
            Logger.log_error(f"Error fetching commentary for match {match_id}: {e}")
            raise e

    def fetch_match_header(self, match_id: int) -> dict:
        """
        Fetches the match data from the database
        """
        try:
            match = self.db.matches.find_one({"_id": match_id})
            return match["matchHeader"] if match else {}
        except Exception as e:
            Logger.log_error(f"Error fetching match header for match {match_id}: {e}")
            raise e

    def add_user_if_not_exists(self, user_id: str, match_id: str) -> dict:
        """
        Adds a user to the database if not already exists
        """
        try:
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
        except Exception as e:
            Logger.log_error(f"Error adding user {user_id}: {e}")
            raise e

    def add_match_id_if_not_exists(self, user_id: str, match_id: str):
        """
        Adds a match ID to a user if it doesn't already exist
        """
        try:
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
        except Exception as e:
            Logger.log_error(f"Error adding match ID {match_id} to user {user_id}: {e}")
            raise e

    def fetch_user(self, user_id: str, match_id: str) -> dict:
        """
        Fetches user data from the database, adds user/match ID if necessary, and returns user data
        """
        try:
            user_data = self.add_user_if_not_exists(user_id, match_id)
            self.add_match_id_if_not_exists(user_id, match_id)
            return (
                user_data
                if user_data is not None
                else self.db.users.find_one({"_id": user_id})
            )
        except Exception as e:
            Logger.log_error(f"Error fetching user {user_id}: {e}")
            raise e

    def fetch_user_notifications(self, user_id: str, match_id: str) -> dict:
        """
        Fetches the notifications sent to the user for a specific match
        """
        try:
            user_data = self.db.users.find_one({"_id": user_id})
            if user_data and "notifications" in user_data:
                match_notifications = user_data["notifications"].get(match_id, {})
                return match_notifications.get("sentNotifications", {})
            return {}
        except Exception as e:
            Logger.log_error(
                f"Error fetching notifications for user {user_id} and match {match_id}: {e}"
            )
            raise e

    def update_user_notifications(
        self, user_id: str, match_id: str, notifications: dict, timestamp: int
    ) -> None:
        """
        Updates the notifications sent to the user
        """
        try:
            self.db.users.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        f"notifications.{match_id}.sentNotifications": notifications,
                        f"notifications.{match_id}.lastNotificationSent": timestamp,
                    }
                },
            )
        except Exception as e:
            Logger.log_error(
                f"Error updating notifications for user {user_id} and match {match_id}: {e}"
            )
            raise e

    def remove_match_id(self, user_id: str, match_id: str) -> None:
        """
        Removes a match ID from the user's data
        """
        try:
            self.db.users.update_one(
                {"_id": user_id}, {"$pull": {"matchIds": match_id}}
            )
            self.db.users.update_one(
                {"_id": user_id}, {"$unset": {f"notifications.{match_id}": ""}}
            )
        except Exception as e:
            Logger.log_error(
                f"Error removing match ID {match_id} from user {user_id}: {e}"
            )
            raise e

    def add_match_id(self, user_id: str, match_id: str) -> None:
        """
        Adds a match ID to the user's data
        """
        try:
            self.db.users.update_one(
                {"_id": user_id}, {"$push": {"matchIds": match_id}}
            )
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
        except Exception as e:
            Logger.log_error(f"Error adding match ID {match_id} to user {user_id}: {e}")
            raise e

    def clear_match_ids(self, user_id: str) -> None:
        """
        Clears all the match IDs from the user's data
        """
        try:
            self.db.users.update_one({"_id": user_id}, {"$set": {"matchIds": []}})
            self.db.users.update_one({"_id": user_id}, {"$set": {"notifications": {}}})
        except Exception as e:
            Logger.log_error(f"Error clearing match IDs for user {user_id}: {e}")
            raise e

    def close(self):
        """
        Closes the database connection
        """
        try:
            self.client.close()
        except Exception as e:
            Logger.log_error(f"Error closing database connection: {e}")
            raise e
