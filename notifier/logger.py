import inspect
import logging
import os
import sys


class Logger:
    __instance = None
    __filename = None

    @classmethod
    def get_instance(cls) -> logging.Logger:
        """
        Returns the instance of the Logger class
        """
        if cls.__instance is None:
            raise ValueError(
                "Cannot get instance before creating one. Use Logger(filename) to create an instance."
            )
        return cls.__instance

    def __init__(self, filename: str) -> None:
        if Logger.__filename is not None and Logger.__filename != filename:
            raise ValueError(
                "Cannot create multiple instances of Logger. Use Logger.get_instance() to get the instance."
            )
        Logger.__filename = filename

        time_stamp_format = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(filename)s: %(message)s",
            datefmt=time_stamp_format,
        )

        if Logger.__instance is None:
            logging.basicConfig(filename=filename, level=logging.DEBUG)
            logger = logging.getLogger()
            logger.handlers[0].setFormatter(formatter)

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            Logger.__instance = logger

    @classmethod
    def clear_log_file(cls) -> bool:
        """
        Clears the log file
        """
        try:
            with open(cls.__filename, mode="w", encoding="utf-8") as file:
                file.truncate(0)
            return True
        except Exception as e:
            cls.log_exception(f"Error occurred while clearing log file: {e}")
            return False

    @classmethod
    def delete_log_file(cls) -> bool:
        """
        Deletes the log file
        """
        try:
            os.remove(cls.__filename)
            return True
        except Exception as e:
            cls.log_exception(f"Error occurred while deleting log file: {e}")
            return False

    @classmethod
    def log_debug(cls, message: str) -> None:
        """
        Logs a debug message
        """
        func_name = inspect.stack()[1][3]
        cls.__instance.debug(f"{func_name}: {message}")

    @classmethod
    def log_info(cls, message: str) -> None:
        """
        Logs an info message
        """
        func_name = inspect.stack()[1][3]
        cls.__instance.info(f"{func_name}: {message}")

    @classmethod
    def log_error(cls, message: str) -> None:
        """
        Logs an error message
        """
        func_name = inspect.stack()[1][3]
        cls.__instance.error(f"{func_name}: {message}")

    @classmethod
    def log_exception(cls, message: str) -> None:
        """
        Logs an exception message
        """
        func_name = inspect.stack()[1][3]
        cls.__instance.exception(f"{func_name}: {message}")
