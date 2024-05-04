import hashlib

from database import Database
from filehandler import Filehandler

mongodb = Database()


class Notifier:
    def notify(self, user_id: str, match_id: str, message: str, timestamp: int) -> None:
        """
        Notifies the user
        """
        unique, notifications = self._check_notification_unique(
            user_id, match_id, timestamp
        )
        print(unique, notifications)
        if unique:
            print(message)
            file = Filehandler.get_instance(user_id)
            file.append_to_file(message)
            notification_hash = self._generate_hash(user_id, match_id, timestamp)
            notifications[notification_hash] = timestamp
            mongodb.update_user_notifications(
                user_id, match_id, notifications, timestamp
            )

    def _check_notification_unique(
        self, user_id: str, match_id: str, timestamp: int
    ) -> tuple:
        """
        Checks if a notification is unique in the user's notifications
        """
        notifications = mongodb.fetch_user_notifications(user_id, match_id)
        notification_hash = self._generate_hash(user_id, match_id, timestamp)
        print(notification_hash not in notifications)
        if notification_hash not in notifications:
            return True, notifications
        return False, notifications

    def _generate_hash(self, user_id: str, match_id: str, timestamp: int) -> str:
        """
        Generates a SHA-256 hash for the notification
        """
        data = f"{user_id}-{match_id}-{timestamp}"
        hash_object = hashlib.sha256(data.encode())
        return hash_object.hexdigest()
