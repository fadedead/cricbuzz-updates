import os

from dotenv import load_dotenv


class Environment:
    _instance = None

    def __new__(cls, env_file=".env"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.env_file = env_file
            cls._instance.load_environment()
        return cls._instance

    def load_environment(self) -> None:
        """
        Loads the environment variables from the .env file
        """
        load_dotenv(self.env_file)
        self.mongo_protocol = os.getenv("MONGO_PROTOCOL")
        self.mongo_user = os.getenv("MONGO_USER")
        self.mongo_pwd = os.getenv("MONGO_PWD")
        self.mongo_host = os.getenv("MONGO_HOST")
        self.mongo_options = os.getenv("MONGO_OPTIONS")

    def get_mongo_uri(self) -> str:
        """
        Returns the mongo uri
        """
        mongo_uri = f"{self.mongo_protocol}://{self.mongo_user}:{self.mongo_pwd}@{self.mongo_host}/?{self.mongo_options}"
        return mongo_uri

    @classmethod
    def get_instance(cls) -> object:
        """
        Returns the instance of the Environment class
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
