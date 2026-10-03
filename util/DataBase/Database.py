from util.Game.Player import DeckData, UserInfo

from .CloudDatabase import CloudDatabase
from .LocalDatabase import LocalDatabase
from typing import NamedTuple
import queue
import threading
import hashlib
import uuid
from datetime import datetime, timezone


class Response(NamedTuple):
    action: str  # "register" or "login"
    success: bool
    message: str
    user_data: dict[str, str] | None = None

class MasterDatabase():
    def __init__(self) -> None:
        self.local: LocalDatabase = LocalDatabase()
        self.cloud: CloudDatabase = CloudDatabase()
        
        # Thread-safe queue for sending results back to the Pygame main loop
        self.response_queue: queue.Queue[Response] = queue.Queue()

    @staticmethod
    def generate_uid() -> str:
        return str(uuid.uuid4())
    
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(data=password.encode(encoding="utf-8")).hexdigest()
    
    @staticmethod
    def get_current_timestamp() -> str:
        return datetime.now(tz=timezone.utc).isoformat()
    
    def save_settings(self, music_vol: float, sfx_vol: float, fps: str, font: str) -> None:
        # Save the settings to the local database
        self.local.save_settings(music_vol, sfx_vol, fps, font)
    
    def get_settings(self) -> dict[str, float | int | str] | None:
        # Retrieve the settings from the local database
        return self.local.get_settings()
    
    def username_exists(self, username: str) -> None:
        def _task() -> None:
            if self.cloud.username_exists(username=username):
                self.response_queue.put(item=Response(action="check_username", success=True, message="The username is already taken"))
            else:
                self.response_queue.put(item=Response(action="check_username", success=False, message="Available"))
            return
        threading.Thread(target=_task, daemon=True).start()
        return
    
    def sign_in(self, username: str, password: str) -> None:
        password_hash: str = self.hash_password(password)
        def _task() -> None:
            success, user_data, message = self.cloud.verify_credentials(username, password_hash)
            
            if success and user_data:
                # 3. Save the incoming cloud data into the local database
                # (Make sure 'save_user_data' matches whatever method name your LocalDatabase uses)
                try:
                    self.local.save_user_auth_data(user_id=user_data.get("id", ""), username=user_data.get("username", ""), password_hash=user_data.get("password", ""), timestamp=self.get_current_timestamp())
                except Exception as e:
                    print(f"Warning: Could not save to local database: {e}")

                # 4. Send success back to Pygame loop
                #print("Success")
                self.response_queue.put(item=Response(action="sign_in", success=True, message=message, user_data=user_data))
            else:
                #print(message)
                # 5. Send failure back to Pygame loop
                self.response_queue.put(item=Response(action="sign_in", success=False, message=message, user_data=None))
            return
            
        threading.Thread(target=_task, daemon=True).start()
        return
    
    def sign_up(self, username: str, password: str, security_code: int) -> None:
        uid = self.generate_uid()
        hashed_password = self.hash_password(password)
        timestamp = self.get_current_timestamp()
        str_security_code = str(security_code)

        def _task() -> None:
            # 1. Check if the username already exists in the cloud database
            if self.cloud.username_exists(username):
                print(f"Registration Failed: Username '{username}' already exists.")
                self.response_queue.put(item=Response(action="sign_up", success=False, message="Username is already taken.", user_data=None))
                return 

            # 2. Attempt to register the user in the cloud
            cloud_success = self.cloud.register_new_user(username=username, user_id=uid, password_hash=hashed_password, timestamp=timestamp, security_code=str_security_code)

            if cloud_success:
                # 3. If cloud succeeds, cache the user locally for future offline verification
                try:
                    self.local.save_user_auth_data(username=username, user_id=uid, password_hash=hashed_password, timestamp=timestamp)
                except Exception as e:
                    print(f"Warning: Could not save to local database: {e}")

                # 4. Build the flat user data dictionary to pass back to the game
                user_data = {
                    "id": uid,
                    "username": username,
                    "password": hashed_password,
                    "lastAuth": timestamp,
                    "security_code": str_security_code
                }

                # 5. Send success response to Pygame main loop
                print("Registration Success")
                self.response_queue.put(item=Response(action="sign_up", success=True, message="Registration successful.", user_data=user_data))
            else:
                # 6. Send failure response to Pygame main loop
                print("Registration Failed: Cloud write error")
                self.response_queue.put(item=Response(
                    action="sign_up", 
                    success=False, 
                    message="Cloud: Failed to register user.", 
                    user_data=None
                ))
            return

        # Start the background thread
        threading.Thread(target=_task, daemon=True).start()
        return
    
    def create_new_deck(self, user_id: str, deck_data: DeckData) -> None:
        def _task() -> None:
            success: bool = self.cloud.create_user_decks(user_id=user_id, deck_data=[deck_data])
            if success:
                self.response_queue.put(item=Response(action="create_deck", success=True, message="Deck created successfully.", user_data=None))
            else:
                self.response_queue.put(item=Response(action="create_deck", success=False, message="Failed to create deck.", user_data=None))
            return
        
        threading.Thread(target=_task, daemon=True).start()
        return
    
    def update_deck(self, deck_id: str, deck_data: DeckData) -> None:
        def _task() -> None:
            success: bool = self.cloud.update_deck(deck_id=deck_id, deck_data=deck_data)
            if success:
                self.response_queue.put(item=Response(action="update_deck", success=True, message="Deck updated successfully.", user_data=None))
            else:
                self.response_queue.put(item=Response(action="update_deck", success=False, message="Failed to update deck.", user_data=None))
            return
        
        threading.Thread(target=_task, daemon=True).start()
        return
    
    def get_user_info(self, user_id: str) -> None:
        def _task() -> None:
            success, user_info, message = self.cloud.get_user_info(user_id=user_id)
            if success and user_info:
                
                self.response_queue.put(item=Response(action="get_user_info", success=True, message=message, user_data=UserInfo(xp=int(user_info.get("xp", 0)), level=int(user_info.get("level", 1), active_deck_uid=user_info.get("activeDeckUid", ""), deck_list_uid=user_info.get("deckListUid", []))))
            else:
                self.response_queue.put(item=Response(action="get_user_info", success=False, message=message, user_data=None))
            return
        
        threading.Thread(target=_task, daemon=True).start()
        return
    
    def update_user_info(self, user_id: str, xp: int | None = None, active_deck_uid: str | None = None, deck_list_uid: list[str] | None = None) -> None:
        def _task() -> None:
            success: bool = self.cloud.update_user_info(user_id=user_id, xp=xp, active_deck_uid=active_deck_uid, deck_list_uid=deck_list_uid)
            if success:
                self.response_queue.put(item=Response(action="update_user_info", success=True, message="User info updated successfully.", user_data=None))
            else:
                self.response_queue.put(item=Response(action="update_user_info", success=False, message="Failed to update user info.", user_data=None))
            return
        
        threading.Thread(target=_task, daemon=True).start()
        return
