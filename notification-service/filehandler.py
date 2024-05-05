class Filehandler:
    _instances = {}

    def __init__(self, filename):
        self.filename = filename
        # Create the file if it doesn't exist
        with open(self.filename, "a"):
            pass

    @classmethod
    def get_instance(cls, filename) -> object:
        """
        Returns the instance of the Filehandler class for the given filename.
        If an instance doesn't exist, creates a new one.
        """
        if filename not in cls._instances:
            cls._instances[filename] = cls(filename)
        return cls._instances[filename]

    def append_to_file(self, data: str) -> None:
        """
        Appends data to the file
        """
        with open(self.filename, "a") as file:
            file.write(data + "\n")
