

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
    active_deck_uid: str # uid of the currently selected deck for the user
    deck_list_uid: list[str]  # List of deck UIDs associated with the user

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
        return self.user_info.get("xp") // 100

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