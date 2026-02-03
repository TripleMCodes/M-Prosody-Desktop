import time
import requests
import json
import os
from pathlib import Path
import keyring #secure os level storage for tokens
import logging
logging.basicConfig(level=logging.DEBUG)

API_BASE = "http://localhost:8000"
TOKEN_SERVICE = "LyricalLabDeskTop"

#paths 
LOCAL_PROJECTS_DIR = Path.home() / ".lyrical_lab" / "projects"
LOCAL_PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


class TokenManager:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.expiry = None
        self.load_tokens()
    
    def load_tokens(self):
        """Load tokens securely from os keyring"""
        self.access_token = keyring.get_password(TOKEN_SERVICE, "access_token")
        self.refresh_token = keyring.get_password(TOKEN_SERVICE, "refresh_token")
        expiry_str = keyring.get_password(TOKEN_SERVICE, "expiry")
        self.expiry = float(expiry_str) if expiry_str else None


    def save_tokens(self):
        """Save tokens securely"""
        if self.access_token is not None:
            keyring.set_password(TOKEN_SERVICE, "access_token", str(self.access_token))
        if self.refresh_token is not None:
            keyring.set_password(TOKEN_SERVICE, "refresh_token", str(self.refresh_token))
        if self.expiry is not None:
            keyring.set_password(TOKEN_SERVICE, "expiry", str(self.expiry))


    def is_access_valid(self):
        """Check if access token is still valid"""
        if not self.access_token or not self.expiry:
            return False
        return time.time() < self.expiry - 10 # buffer for 10s


    def refresh_access(self):
        """Use refresh token to get new access token"""
        #refresh token to mint a new access token
        if not self.refresh_token:
            return False
        try:
            resp = requests.post(
                f"{API_BASE}/auth/refresh",
                json={"refresh_token": self.refresh_token},
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data["access_token"]
                self.expiry = time.time() + float(data.get("expires_in", 3600))
                self.refresh_token = data.get("refresh_token", self.refresh_token)
                self.save_tokens()
                return True
            return False
        except requests.RequestException:
            return False

        
    def ensure_access(self):
        """Ensure we have a valid access token"""
        if self.is_access_valid():
            return True
        return self.refresh_access()
    
# API client

class LyricalLabAPI:

    def __init__(self):
        self.token = TokenManager()

    def get_headers(self):
        if self.token.ensure_access():
            return {"Authorization":
                    f"Bearer {self.token.access_token}" }
        return {} #offline / no login
    
    def call_endpoint(self, endpoint, data=None, access_token_required=True, login=True):
        """Call online API if available"""

        # Only require token for endpoints that need it
        if access_token_required:
            headers = self.get_headers()
            if not headers:
                logging.debug("Offline mode or no valid token")
                print(self.token.access_token)
                print("Offline mode or no valid token")
                return None
        else:
            headers = {}

        try:
            url = f"{API_BASE}{endpoint}"

            if login:
                print("logging...")
                # Send FORM fields
                resp = requests.post(
                    url,
                    data=data,
                    headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
                    timeout=5
                )
            else:
                print("signing up...")
                resp = requests.post(
                    url,
                    json=data, 
                    headers={**headers, "Content-Type": "application/json"},
                    timeout=5
                )

            if not resp.ok:
                print("Status:", resp.status_code)
                print("Response:", resp.text)

            if resp.status_code == 401 and access_token_required:
                if self.token.refresh_access():
                    headers = self.get_headers()
                    resp = requests.post(url, json=data, headers=headers, timeout=5)
                else:
                    logging.debug("Login required for online features")
                    return None

            print("Done")
            return resp.json()

        except requests.RequestException as e:
            logging.debug(f"API unavailable, offline mode active: {e}")
            return None

#test 

def main():
    api = LyricalLabAPI()

    #offline, use local features
    logging.debug("Working offline/local features")

    local_projects = list(LOCAL_PROJECTS_DIR.glob("*.json"))
    logging.debug(f'Found {len(local_projects)} local projects')

    #online call lexical endpoint

    logging.debug("Trying online lexical feature...")
    data = {"word": "light"}
    result = api.call_endpoint("/lexical/rhymes", data)
    if result:
        logging.debug("Online rhymes:", result)
    else:
        logging.debug("Offline / could not fetch rhymes")
    
if __name__ == "__main__":
    main()
