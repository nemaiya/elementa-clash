import uuid
import hashlib
import requests
from datetime import datetime, timezone
from requests.models import Response
from util.Game.Player import DeckData, UserInfo

PROJECT_ID = "elementa-clash"

class CloudDatabase():
    def __init__(self) -> None:
        # Only keeping the Realtime DB URL
        self.realtime_url: str = f"https://{PROJECT_ID}-default-rtdb.firebaseio.com"
    
    def username_exists(self, username: str) -> bool:
        url: str = f"{self.realtime_url}/users/{username}.json"
        try:
            res: Response = requests.get(url, timeout=4)
            # In RTDB, a missing path returns 200 OK but with a body of 'null'
            return res.status_code == 200 and res.json() is not None
        except requests.RequestException:
            return False
        
    def register_new_user(self, username: str, user_id: str, password_hash: str, timestamp: str, security_code: str) -> bool:
        url: str = f"{self.realtime_url}/users/{username}.json"
        
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
        url: str = f"{self.realtime_url}/users/{username}.json"
        
        try:
            res: Response = requests.get(url, timeout=4)
            
            if res.status_code != 200:
                return False, None, f"Cloud: Database error {res.status_code} - {res.text}"
            
            data = res.json()
            
            # 1. Check if user exists (RTDB returns None/null if path doesn't exist)
            if data is None:
                return False, None, f"Cloud: User '{username}' does not exist."
            
            # 2. Extract data directly
            cloud_password = data.get("password")
            
            # 3. Compare the hashes
            if cloud_password == password_hash:
                flat_user_data = {
                    "id": data.get("id", ""),
                    "username": data.get("username", ""),
                    "password": cloud_password,
                    "lastAuth": data.get("lastAuth", ""),
                    "security_code": data.get("security_code", "")
                }
                return True, flat_user_data, "Login Successful"
            else:
                return False, None, f"Cloud: Password mismatch for '{username}'."
                
        except requests.RequestException as e:
            return False, None, f"Cloud: Network error - {e}"
    
    def create_new_user_info(self, user_id: str, xp: int, active_deck_uid: str, deck_list_uid: list[str]) -> bool:
        url: str = f"{self.realtime_url}/users/{user_id}.json"
        payload: dict[str, int | str | list[str]] = {
            "id": user_id,
            "xp": xp,
            "activeDeckUid": active_deck_uid,
            "deckListUid": deck_list_uid
        }
        try:
            res: Response = requests.put(url, json=payload, timeout=4)
            return res.status_code == 200
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return False
    
    def get_user_info(self, user_id: str) -> tuple[bool, UserInfo | None, str]:
        url: str = f"{self.realtime_url}/users/{user_id}.json"
        try:
            res: Response = requests.get(url, timeout=4)
            if res.status_code != 200:
                return False, None, f"Cloud: Database error {res.status_code} - {res.text}"

            data = res.json()
            if data is None or not isinstance(data, dict):
                return False, None, f"Cloud: User '{user_id}' does not exist."

            deck_list_raw = data.get("deckListUid", [])
            deck_list_uid: list[str] = [
                str(uid) for uid in deck_list_raw if isinstance(deck_list_raw, list)
            ] if isinstance(deck_list_raw, list) else []

            user_info = UserInfo(
                uid=str(data.get("id", user_id)),
                xp=int(data.get("xp", 0) or 0),
                active_deck_uid=str(data.get("activeDeckUid", "")),
                deck_list_uid=deck_list_uid,
            )
            return True, user_info, "User info retrieved successfully."
        except requests.RequestException as e:
            return False, None, f"Cloud: Network error - {e}"
    
    def update_user_info(self, user_id: str, xp: int | None = None, active_deck_uid: str | None = None, deck_list_uid: list[str] | None = None) -> bool:
        url: str = f"{self.realtime_url}/users/{user_id}.json"
        payload: dict[str, int | str | list[str]] = {}
        
        if xp is not None:
            payload["xp"] = xp
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
                
            url: str = f"{self.realtime_url}/decks/{deck_id}.json"

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
            
        url: str = f"{self.realtime_url}/decks/{deck_id}.json"

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