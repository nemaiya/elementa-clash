

from typing import TypedDict

class DeckData(TypedDict):
    user_id: str # Store the user uid for reference
    uid: str # Store the deck uid as well
    name: str # Store the name of the deck
    characters: list[str] # Expects exactly 3 character IDs/names
    action_cards: list[str] # Expects exactly 10 action/equipment card IDs/names

class UserInfo(TypedDict):
    uid: str # Stores the user id
    xp: int  # the xp value of the user, used to calculate level
    battle_wins: int # the number of battles won by the user
    total_battles: int # the total number of battles played by the user
    active_deck_uid: str # uid of the currently selected deck for the user
    deck_list_uid: list[str]  # List of deck UIDs associated with the user

class LeaderboardEntry(TypedDict):
    uid: str
    username: str
    xp: int
    battle_wins: int
    total_battles: int

class Player:
    def __init__(self, uid: str, username: str, user_info: UserInfo, user_decks: list[DeckData]) -> None:
        # Stores the player's unique identifier, username, user information, and associated decks.
        self.uid: str = uid
        self.username: str = username
        self.user_info: UserInfo = user_info
        self.user_decks: list[DeckData] = user_decks
        self.selected_deck: DeckData | None = None
        for deck in user_decks:
            if deck.get("uid") == self.user_info.get("active_deck_uid"):
                self.selected_deck = deck
                break
        if self.selected_deck is None and user_decks:
            self.selected_deck = user_decks[0]
            self.user_info["active_deck_uid"] = user_decks[0]["uid"]

    @property
    def level(self) -> int:
        return self.user_info.get("xp", 0) // 100

    @staticmethod
    def battle_xp(elapsed_ms: int, characters_alive: int) -> int:
        # Faster wins keep more of the time bonus; leftover characters add extra XP.
        seconds: int = max(0, elapsed_ms // 1000)
        time_xp: int = max(10, 80 - seconds // 2)
        alive_xp: int = max(0, characters_alive) * 25
        return time_xp + alive_xp

    def record_battle(self, won: bool, elapsed_ms: int = 0, characters_alive: int = 0) -> int:
        """Updates local user_info after a battle. Returns XP gained this battle."""
        self.user_info["total_battles"] = int(self.user_info.get("total_battles", 0)) + 1
        xp_gained: int = 0
        if won:
            self.user_info["battle_wins"] = int(self.user_info.get("battle_wins", 0)) + 1
            xp_gained = self.battle_xp(elapsed_ms=elapsed_ms, characters_alive=characters_alive)
            self.user_info["xp"] = int(self.user_info.get("xp", 0)) + xp_gained
        return xp_gained

    def is_deck_slot_unlocked(self, slot_no: int) -> bool:
        """
        Evaluates the level constraints for the 4 available deck slots.
        Slot 0 (Deck 1): Free
        Slot 1 (Deck 2): Free
        Slot 2 (Deck 3): Unlocks at Level 3
        Slot 3 (Deck 4): Unlocks at Level 4
        """
        if slot_no < 3:
            return True
        elif slot_no == 3:
            return self.level >=3
        elif slot_no == 4:
            return self.level >=4
        else:
            return False


class GamePlayer():
    pass