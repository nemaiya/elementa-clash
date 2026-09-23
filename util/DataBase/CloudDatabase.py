import uuid

from requests.models import Response
import hashlib
from datetime import datetime, timezone
import requests


PROJECT_ID = "elementa-clash"
class CloudDatabase():
    def __init__(self) -> None:
        self.realtime_url: str = f"https://{PROJECT_ID}-default-rtdb.firebaseio.com"
        
        self.firestore_url: str = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"
    
    def username_exists(self, username: str) -> bool:
        url: str = f"{self.firestore_url}/users/{username}"
        try:
            res: Response = requests.get(url, timeout=4)
            return res.status_code == 200
        except requests.RequestException:
            return False
        
    def register_new_user(self, username: str, user_id: str, password_hash: str, timestamp: str, security_code: str) -> bool:
        url: str = f"{self.firestore_url}/users/{username}"
        
        # Firestore REST API strictly requires you to define the data type for every field
        payload = {
            "fields": {
                "id": {"stringValue": user_id},
                "username": {"stringValue": username},
                "password": {"stringValue": password_hash},
                "lastAuth": {"stringValue": timestamp},
                "createdAt": {"stringValue": timestamp},
                "security_code": {"stringValue": security_code}
            }
        }

        try:
            res: Response = requests.patch(url, json=payload, timeout=4)
            if res.status_code != 200:
                print(f"Error {res.status_code}: {res.text}") # <--- ADD THIS LINE
            return res.status_code == 200
        except requests.RequestException as e:
            print(f"Request failed: {e}") # <--- ADD THIS LINE
            return False
    
    def verify_credentials(self, username: str, password_hash: str) -> tuple[bool, dict[str, str] | None, str]:
        url: str = f"{self.firestore_url}/users/{username}"
        
        try:
            res: Response = requests.get(url, timeout=4)
            
            # 1. Check if user even exists
            if res.status_code == 404:
                return False, None, f"Cloud: User '{username}' does not exist."
            elif res.status_code != 200:
                return False, None, f"Cloud: Database error {res.status_code} - {res.text}"
            
            # 2. Extract data
            data = res.json().get("fields", {})
            cloud_password = data.get("password", {}).get("stringValue")
            
            # 3. Compare the hashes!
            if cloud_password == password_hash:
                flat_user_data = {
                    "id": data.get("id", {}).get("stringValue", ""),
                    "username": data.get("username", {}).get("stringValue", ""),
                    "password": cloud_password,
                    "lastAuth": data.get("lastAuth", {}).get("stringValue", ""),
                    "security_code": data.get("security_code", {}).get("stringValue", "")
                }
                return True, flat_user_data, "Login Successful"
            else:
                return False, None, f"Cloud: Password mismatch for '{username}'."
                
        except requests.RequestException as e:
            return False, None, f"Cloud: Network error - {e}"

    

if __name__ == "__main__":
    db: CloudDatabase = CloudDatabase()
    _ = db.register_new_user(username="sadiq7", user_id=str(uuid.uuid4()), password_hash=hashlib.sha256(data=("sadiq2009").encode(encoding="utf-8")).hexdigest(), timestamp=datetime.now(tz=timezone.utc).isoformat(), security_code="676767")
    print(_)