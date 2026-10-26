"""Create API key credentials and generate the first API key (slot 1)."""
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


# #region sign-in
# Sign in
load_dotenv()  # reads .env
PORTAL = os.environ["PORTAL"]
USERNAME = os.environ["ITEM_OWNER"]
token = post(
    "/oauth2/token",
    client_id=os.environ["APP_CLIENT_ID"],
    client_secret=os.environ["APP_CLIENT_SECRET"],
    grant_type="client_credentials",
)["access_token"]
# #endregion sign-in

# #region add-item
# Create the credential item
# Portal wizard › Item details: title, tags and description
item_id = post(
    f"/content/users/{USERNAME}/addItem",
    type="Application",
    title="My API key credentials tutorial",
    tags="api key,basemaps,geocoding",
    snippet="Key for the store locator app",
    token=token,
)["id"]
# #endregion add-item

# #region register
# Register the item as an app
# Portal wizard › Privileges: services the key can call (+ portal:app:access:item:<id> per item)
PRIVILEGES = "premium:user:basemaps,premium:user:geocode"  # @var privileges

app = post(
    "/oauth2/registerApp",
    itemId=item_id,
    appType="multiple",
    redirect_uris=json.dumps(["urn:ietf:wg:oauth:2.0:oob"]),
    privileges=json.dumps([p.strip() for p in PRIVILEGES.split(",")]),
    # Portal wizard › Settings: empty = any site can use the key. Set your app's URL(s) before you ship
    httpReferrers=json.dumps([]),
    token=token,
)
client_id, client_secret = app["client_id"], app["client_secret"]
# #endregion register

# #region expiration
# Set the expiration of slot 1
# Portal wizard › Settings: expiration date (max. 1 year)
expires = int((time.time() + 30 * 86400) * 1000)  # 30 days from now, epoch ms
post(
    f"/content/users/{USERNAME}/items/{item_id}/update",
    apiToken1ExpirationDate=expires,
    token=token,
)
# #endregion expiration

# #region generate
# Generate the API key
# Portal wizard › Generate API key: generate the key in slot 1 now
api_key = post(
    "/oauth2/token",
    client_id=client_id,
    client_secret=client_secret,
    grant_type="client_credentials",
    apiToken=1,
    regenerateApiToken="false",
)["access_token"]

print("Item ID:", item_id)
print("API key (slot 1):", api_key)

# state.json is written by the scripts, unlike .env. It doesn't hold the key: deploy that to your app
# state.json: {"itemId": "a1f3c9e27b8d4e6f9c0b2d4e6f8a1c3e", "slot": 1}
with open("state.json", "w") as f:
    json.dump({"itemId": item_id, "slot": 1}, f, indent=2)
# #endregion generate
