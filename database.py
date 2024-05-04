from bson.objectid import ObjectId
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

    def check_match_exists(self, match_id: int) -> dict:
        """
        Checks if a match exists in the database
        """
        return self.db.matches.find_one({"_id": match_id})

    def insert_match(self, match: dict):
        """
        Inserts a match into the database
        """
        match_id = match["matchHeader"]["matchId"]
        match["_id"] = match_id
        match["fullCommentaryExists"] = False
        self.db.matches.insert_one(match)

    def update_full_commentary(self, match_id: int, commentary: list):
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

                # Update match fullCommentaryExists to True
                self.db.matches.update_one(
                    {"_id": match_id},
                    {"$set": {"fullCommentaryExists": True}},
                    session=session,
                )
                # Commit transaction
                session.commit_transaction()
        except Exception as e:
            print(f"Transaction aborted: {e}")
            session.abort_transaction()

    def close(self):
        self.client.close()
