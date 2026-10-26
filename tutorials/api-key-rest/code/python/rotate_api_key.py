"""Rotate an API key: generate a key in the free slot, deploy it, then invalidate the old one."""
import json
import os
import time

import requests
from dotenv import load_dotenv

def post(path, **params):
    """POST a form to the portal and print the response when VERBOSE=1.
    ArcGIS reports errors inside HTTP 200 responses."""
    response = requests.post(f"{PORTAL}{path}", data={"f": "json", **params})
    response.raise_for_status()
    data = response.json()
    if os.environ.get("VERBOSE"):  # prints secrets: don't enable it where logs are kept
        print(json.dumps(data, indent=2))
    if "error" in data:
        raise RuntimeError(data["error"])
    return data


# #region rotate-config
# Rotate: start from the key in production
load_dotenv()  # reads .env
PORTAL = os.environ["PORTAL"]
USERNAME = os.environ["ITEM_OWNER"]

# Item and slot of the key in production, saved by create_api_key.py
# state.json: {"itemId": "a1f3c9e27b8d4e6f9c0b2d4e6f8a1c3e", "slot": 1}
with open("state.json") as f:
    state = json.load(f)
ITEM_ID = state["itemId"]
# #endregion rotate-config

# #region app-info
# Get the item's client credentials
token = post(
    "/oauth2/token",
    client_id=os.environ["APP_CLIENT_ID"],
    client_secret=os.environ["APP_CLIENT_SECRET"],
    grant_type="client_credentials",
)["access_token"]

app = post(f"/content/users/{USERNAME}/items/{ITEM_ID}/registeredAppInfo", token=token)
client_id, client_secret = app["client_id"], app["client_secret"]
# #endregion app-info

# #region find-slot
# Find the free slot
current_slot = state["slot"]
new_slot = 1 if current_slot == 2 else 2
# #endregion find-slot

# #region rotate-expiration
# Set the expiration of the new slot
expires = int((time.time() + 30 * 86400) * 1000)  # 30 days from now, epoch ms
post(
    f"/content/users/{USERNAME}/items/{ITEM_ID}/update",
    token=token,
    **{f"apiToken{new_slot}ExpirationDate": expires},
)
# #endregion rotate-expiration

# #region rotate-generate
# Generate the key in the new slot
new_key = post(
    "/oauth2/token",
    client_id=client_id,
    client_secret=client_secret,
    grant_type="client_credentials",
    apiToken=new_slot,
    regenerateApiToken="true",
)["access_token"]
print(f"New API key (slot {new_slot}):", new_key)
# #endregion rotate-generate

# #region deploy
# Deploy the new key
input("Deploy the new key, then press Enter to invalidate the old one…")
# #endregion deploy

# #region invalidate
# Invalidate the old key
result = post(
    "/oauth2/revokeToken",
    client_id=client_id,
    client_secret=client_secret,
    apiToken=current_slot,
)
print(f"Old key in slot {current_slot} invalidated:", json.dumps(result.get("success")))

# The key in production is now in the new slot
with open("state.json", "w") as f:
    json.dump({"itemId": ITEM_ID, "slot": new_slot}, f, indent=2)
# #endregion invalidate
