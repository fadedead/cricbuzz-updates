from database import Database

mongodb = Database()


class Menu:
    def __init__(self, active_match_ids, non_active_match_ids):
        self.active_matches = active_match_ids
        self.non_active_matches = non_active_match_ids

    def get_match_name(self, match_id) -> str:
        """
        Returns the match name for the given match ID
        """
        match_header = mongodb.fetch_match_header(match_id)
        team1 = match_header.get("team1", {}).get("shortName", "")
        team2 = match_header.get("team2", {}).get("shortName", "")
        return f"{team1} vs {team2}"

    def menu(self) -> tuple:
        """
        Menu function
        """
        active_matches = [
            f"{match_id}: {self.get_match_name(match_id)}"
            for match_id in self.active_matches
        ]
        non_active_matches = [
            f"{match_id}: {self.get_match_name(match_id)}"
            for match_id in self.non_active_matches
        ]

        print("Inactive matches:")
        if not non_active_matches:
            print("No matches")
        else:
            for match in non_active_matches:
                print(match)
        print("\n" * 2)

        print("Active matches:")
        if not active_matches:
            print("No active matches")
        else:
            for match in active_matches:
                print(match)
        print("\n" * 2)

        print("1. Fetch commentary for non-active matches")
        print("2. Fetch commentary for active matches")
        print("3. Exit")

        return self._handle_input()

    def _handle_input(self) -> tuple:
        choice = input("Enter your choice: ")
        return self._handle_choice(choice)

    def _handle_choice(self, choice) -> tuple:
        """
        Handles the user choice
        """
        if choice == "1":
            id_input = input("Enter the match ID separated by commas (id1, id2):")
            id_list = [int(value.strip()) for value in id_input.split(",")]
            for match_id in id_list:
                if match_id not in self.non_active_matches:
                    print(f"Match {match_id} is not a valid match")
                    print("Please try again.")
                    return self._handle_input()
            return "NON_ACTIVE_MATCHES", id_list
        elif choice == "2":
            id_input = input("Enter the match ID separated by commas (id1, id2):")
            id_list = [int(value.strip()) for value in id_input.split(",")]
            for match_id in id_list:
                if match_id not in self.active_matches:
                    print(f"Match {match_id} is not a valid match")
                    print("Please try again.")
                    return self._handle_input()
            return "ACTIVE_MATCHES", id_list
        elif choice == "3":
            exit()
        else:
            print("Invalid choice. Please try again.")
            return self._handle_input()
