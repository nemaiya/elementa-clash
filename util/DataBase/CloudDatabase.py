import uuid
import hashlib
import requests
from datetime import datetime, timezone
from requests.models import Response
from util.Game.Player import DeckData, LeaderboardEntry, UserInfo

PROJECT_ID = "elementa-clash"

class CloudDatabase():
    def __init__(self) -> None:
        # Store the URL of the cloud database
        self.realtime_url: str = f"https://{PROJECT_ID}-default-rtdb.firebaseio.com"
    
    def username_exists(self, username: str) -> bool:
        url: str = f"{self.realtime_url}/users_auth/{username}.json"
        try:
            res: Response = requests.get(url, timeout=4)
            # In RTDB, a missing path returns 200 OK but with a body of 'null'
            return res.status_code == 200 and res.json() is not None
        except requests.RequestException:
            return False
        
    def register_new_user(self, username: str, user_id: str, password_hash: str, timestamp: str, security_code: str) -> bool:
        url: str = f"{self.realtime_url}/users_auth/{username}.json"
        
        # RTDB takes standard flat JSON - no need for 'stringValue' wrappers
        payload = {
            "id": user_id,
            "username": username,
            "password": password_hash,
            "lastAuth": timestamp,
            "createdAt": timestamp,
            "security_code": security_code
        }

        try:
            res: Response = requests.patch(url, json=payload, timeout=4)
            if res.status_code != 200:
                print(f"Error {res.status_code}: {res.text}")
            return res.status_code == 200
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return False
    
    def verify_credentials(self, username: str, password_hash: str) -> tuple[bool, dict[str, str] | None, str]:
        # Store the URL of the user's authentication data
        url: str = f"{self.realtime_url}/users_auth/{username}.json"
        
        try:
            res: Response = requests.get(url, timeout=4) # Get the user's authentication data
            if res.status_code != 200: # Return False if the user's authentication data is not found
                return False, None, f"Cloud: Database error {res.status_code} - {res.text}"

            data = res.json() # Get the user's authentication data by converting the response to a JSON object
            
            if data is None: # Return False if the user's authentication data is not found
                return False, None, f"Cloud: User '{username}' does not exist."
            
            cloud_password = data.get("password") # Extract the password from the user's authentication data
            
            if cloud_password == password_hash: # Compare the password hash with the user's authentication data
                flat_user_data = { # Create a user data dictionary
                    "id": data.get("id", ""), "username": data.get("username", ""), "password": cloud_password, "lastAuth": data.get("lastAuth", ""), "security_code": data.get("security_code", "")
                }
                return True, flat_user_data, "Login Successful" # Return True if the password hash matches the user's authentication data
            else:
                return False, None, f"Cloud: Password mismatch for '{username}'." # Return False if the password hash does not match the user's authentication data
                
        except requests.RequestException as e:
            return False, None, f"Cloud: Network error - {e}"
    
    def create_new_user_info(self, user: UserInfo) -> bool:
        url: str = f"{self.realtime_url}/users_info/{user['uid']}.json"
        payload: dict[str, int | str | list[str]] = {
            "id": user['uid'],
            "xp": user['xp'],
            "battleWins": user['battle_wins'],
            "totalBattles": user['total_battles'],
            "activeDeckUid": user['active_deck_uid'],
            "deckListUid": user['deck_list_uid']
        }
        try:
            res: Response = requests.put(url, json=payload, timeout=4)
            return res.status_code == 200
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return False
    
    def get_user_info(self, user_id: str) -> tuple[bool, UserInfo | None, str]:
        url: str = f"{self.realtime_url}/users_info/{user_id}.json"
        try:
            res: Response = requests.get(url, timeout=4)
            if res.status_code != 200:
                return False, None, f"Cloud: Database error {res.status_code} - {res.text}"

            data = res.json()
            if data is None or not isinstance(data, dict):
                return False, None, f"Cloud: User '{user_id}' does not exist."

            user_info: UserInfo = UserInfo(
                uid=str(data.get("id", user_id)),
                xp=int(data.get("xp", 0) or 0),
                battle_wins=int(data.get("battleWins", 0) or 0),
                total_battles=int(data.get("totalBattles", 0) or 0),
                active_deck_uid=str(data.get("activeDeckUid", "")),
                deck_list_uid=list(data.get("deckListUid", [])),
            )
            return True, user_info, "User info retrieved successfully."
        except requests.RequestException as e:
            return False, None, f"Cloud: Network error - {e}"
    
    def update_user_info(self, user_id: str, xp: int | None = None, battle_wins: int | None = None, total_battles: int | None = None, active_deck_uid: str | None = None, deck_list_uid: list[str] | None = None) -> bool:
        url: str = f"{self.realtime_url}/users_info/{user_id}.json"
        payload: dict[str, int | str | list[str]] = {}
        
        if xp is not None:
            payload["xp"] = xp
        if battle_wins is not None:
            payload["battleWins"] = battle_wins
        if total_battles is not None:
            payload["totalBattles"] = total_battles
        if active_deck_uid is not None:
            payload["activeDeckUid"] = active_deck_uid
        if deck_list_uid is not None:
            payload["deckListUid"] = deck_list_uid
        
        if not payload:
            print("No fields provided to update.")
            return False
        
        try:
            res: Response = requests.patch(url, json=payload, timeout=4)
            return res.status_code == 200
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return False

    def create_user_decks(self, user_id: str, deck_data: list[DeckData]) -> bool:
        """
        Creates multiple decks for a user.
        deck_data should be a list of dicts.
        """
        success = True
        
        for deck in deck_data:
            deck_id = deck.get("uid")
            if not deck_id:
                print("Skipped a deck because it was missing a 'uid'.")
                success = False
                continue
                
            url: str = f"{self.realtime_url}/user_decks/{deck_id}.json"

            # RTDB accepts arrays natively
            payload = {
                "userId": user_id,
                "deckId": deck_id,
                "name": deck.get("name", ""),
                "chars": deck.get("characters", []),
                "action": deck.get("action_cards", [])
            }

            try:
                # PUT completely overwrites the path, which is perfect for new creations
                res: Response = requests.put(url, json=payload, timeout=4)
                if res.status_code != 200:
                    print(f"Error {res.status_code} creating deck {deck_id}: {res.text}")
                    success = False
            except requests.RequestException as e:
                print(f"Request failed for deck {deck_id}: {e}")
                success = False
                
        return success

    def update_deck(self, deck_id: str, deck_data: DeckData) -> bool:
        """
        Updates an existing deck. Only updates the fields provided in deck_data.
        """
        # Standard dictionary for updates
        fields = {}
        if "name" in deck_data:
            fields["name"] = deck_data["name"]
        if "characters" in deck_data:
            fields["chars"] = deck_data["characters"]
        if "action_cards" in deck_data:
            fields["action"] = deck_data["action_cards"]
            
        if not fields:
            print("No valid fields provided to update.")
            return False
            
        url: str = f"{self.realtime_url}/user_decks/{deck_id}.json"

        try:
            # PATCH in RTDB automatically merges data.
            # It will update 'chars' and 'name' without deleting 'userId' or 'deckId'.
            res: Response = requests.patch(url, json=fields, timeout=4)
            if res.status_code != 200:
                print(f"Error {res.status_code} updating deck {deck_id}: {res.text}")
                return False
            return True
        except requests.RequestException as e:
            print(f"Request failed for updating deck {deck_id}: {e}")
            return False

    def _parse_deck(self, deck_id: str, data: dict[str, object], fallback_user_id: str = "") -> DeckData:
        characters = data.get("chars", data.get("characters", []))
        action_cards = data.get("action", data.get("action_cards", []))
        return DeckData(
            user_id=str(data.get("userId", fallback_user_id)),
            uid=str(data.get("deckId", deck_id)),
            name=str(data.get("name", "")),
            characters=list(characters) if isinstance(characters, list) else [],
            action_cards=list(action_cards) if isinstance(action_cards, list) else [],
        )

    def get_deck(self, deck_id: str, user_id: str = "") -> tuple[bool, DeckData | None, str]:
        url: str = f"{self.realtime_url}/user_decks/{deck_id}.json"
        try:
            res: Response = requests.get(url, timeout=4)
            if res.status_code != 200:
                return False, None, f"Cloud: Database error {res.status_code} - {res.text}"
            data = res.json()
            if data is None or not isinstance(data, dict):
                return False, None, f"Cloud: Deck '{deck_id}' does not exist."
            return True, self._parse_deck(deck_id=deck_id, data=data, fallback_user_id=user_id), "Deck retrieved successfully."
        except requests.RequestException as e:
            return False, None, f"Cloud: Network error - {e}"

    def get_leaderboard_entries(self) -> tuple[bool, list[LeaderboardEntry] | None, str]:
        info_url: str = f"{self.realtime_url}/users_info.json"
        auth_url: str = f"{self.realtime_url}/users_auth.json"
        try:
            info_res: Response = requests.get(info_url, timeout=6)
            auth_res: Response = requests.get(auth_url, timeout=6)
            if info_res.status_code != 200:
                return False, None, f"Cloud: Database error {info_res.status_code} - {info_res.text}"
            if auth_res.status_code != 200:
                return False, None, f"Cloud: Database error {auth_res.status_code} - {auth_res.text}"

            info_data = info_res.json()
            auth_data = auth_res.json()

            id_to_username: dict[str, str] = {}
            if isinstance(auth_data, dict):
                for username, payload in auth_data.items():
                    if not isinstance(payload, dict):
                        continue
                    uid = str(payload.get("id", ""))
                    if uid:
                        id_to_username[uid] = str(payload.get("username", username))

            entries: list[LeaderboardEntry] = []
            if isinstance(info_data, dict):
                for key, payload in info_data.items():
                    if not isinstance(payload, dict):
                        continue
                    uid = str(payload.get("id", key))
                    entries.append(LeaderboardEntry(
                        uid=uid,
                        username=id_to_username.get(uid, "Unknown"),
                        xp=int(payload.get("xp", 0) or 0),
                        battle_wins=int(payload.get("battleWins", 0) or 0),
                        total_battles=int(payload.get("totalBattles", 0) or 0),
                    ))
            return True, entries, "Leaderboard retrieved successfully."
        except requests.RequestException as e:
            return False, None, f"Cloud: Network error - {e}"

    def get_user_decks(self, user_id: str, deck_ids: list[str] | None = None) -> tuple[bool, list[DeckData] | None, str]:
        ids: list[str] = list(deck_ids or [])
        if not ids:
            info_ok, user_info, info_message = self.get_user_info(user_id=user_id)
            if not info_ok or user_info is None:
                return False, None, info_message
            ids = list(user_info["deck_list_uid"])

        decks: list[DeckData] = []
        for deck_id in ids:
            if not deck_id:
                continue
            ok, deck, message = self.get_deck(deck_id=deck_id, user_id=user_id)
            if not ok or deck is None:
                return False, None, message
            decks.append(deck)
        return True, decks, "User decks retrieved successfully."

if __name__ == "__main__":
    db: CloudDatabase = CloudDatabase()
    _ = db.register_new_user(
        username="sadiq7", 
        user_id=str(uuid.uuid4()), 
        password_hash=hashlib.sha256(data=("sadiq2009").encode(encoding="utf-8")).hexdigest(), 
        timestamp=datetime.now(tz=timezone.utc).isoformat(), 
        security_code="676767"
    )
    print(_)