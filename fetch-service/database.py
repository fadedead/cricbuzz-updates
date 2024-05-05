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
            Logger.log_error(f"Error connecting to the database: {e}")
            raise e

    def check_match_exists(self, match_id: int) -> dict:
        """
        Checks if a match exists in the database
        """
        try:
            return self.db.matches.find_one({"_id": match_id})
        except Exception as e:
            Logger.log_error(f"Error checking if match exists: {e}")
            raise e

    def upsert_match(self, match: dict):
        """
        Inserts a match into the database
        """
        try:
            match_id = match["matchHeader"]["matchId"]
            match["_id"] = match_id
            match["fullCommentaryExists"] = False
            self.db.matches.update_one({"_id": match_id}, {"$set": match}, upsert=True)
        except Exception as e:
            Logger.log_error(f"Error inserting match into the database: {e}")
            raise e

    def update_commentary(self, match_id: int, commentary: list) -> None:
        """
        Updates commentary of a match in the database
        """
        session = self.client.start_session()
        try:
            with session.start_transaction():
                # Update the commentary
                self.db.commentaries.update_one(
                    {"_id": match_id},
                    {"$set": {"commentary": commentary}},
                    session=session,
                    upsert=True,
                )

                match = self.db.matches.find_one({"_id": match_id})
                if match["matchHeader"]["state"] != "In Progress":
                    # Update match fullCommentaryExists to True if match is finished
                    self.db.matches.update_one(
                        {"_id": match_id},
                        {"$set": {"fullCommentaryExists": True}},
                        session=session,
                    )

                # Commit transaction
                session.commit_transaction()
        except Exception as e:
            Logger.log_error(
                f"Error updating full commentary for match {match_id}: {e}"
            )
            session.abort_transaction()

    def close(self):
        """
        Closes the database connection
        """
        try:
            self.client.close()
        except Exception as e:
            Logger.log_error(f"Error closing the database connection: {e}")
            raise e
