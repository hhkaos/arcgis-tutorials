"""Create API key credentials and generate the first API key (slot 1)."""
# #region imports
import datetime as dt
import json
import os

from arcgis.gis import GIS, ItemProperties, ItemTypeEnum
from dotenv import load_dotenv
# #endregion imports

# #region sign-in
# Sign in
load_dotenv()  # reads .env
gis = GIS(
    os.environ["PORTAL_URL"],
    client_id=os.environ["APP_CLIENT_ID"],
    client_secret=os.environ["APP_CLIENT_SECRET"],
)
# #endregion sign-in

# #region add-item
# Create the credential item
# Portal wizard › Item details: title, tags and description
folder = gis.content.folders.get()  # your root folder
item = folder.add(
    item_properties=ItemProperties(
        title="My API key credentials tutorial",
        item_type=ItemTypeEnum.APPLICATION,
        tags=["api key", "basemaps", "geocoding"],
        snippet="Key for the store locator app",
    )
).result()
# #endregion add-item

# #region register
# Register the item as an app
# Portal wizard › Privileges: services the key can call (+ portal:app:access:item:<id> per item)
PRIVILEGES = "premium:user:basemaps,premium:user:geocode"  # @var privileges

item.register(
    app_type="multiple",
    redirect_uris=["urn:ietf:wg:oauth:2.0:oob"],
    # Portal wizard › Settings: empty = any site can use the key. Set your app's URL(s) before you ship
    http_referers=[],
    privileges=[p.strip() for p in PRIVILEGES.split(",")],
)
# #endregion register

# #region expiration
# Set the expiration of slot 1
# Portal wizard › Settings: expiration date (max. 1 year)
expiration = dt.datetime.now() + dt.timedelta(days=30)
item.update(item_properties={"apiToken1ExpirationDate": int(expiration.timestamp() * 1000)})
# #endregion expiration

# #region generate
# Generate the API key
# Portal wizard › Generate API key: generate the key in slot 1 now
result = item.generate_api_token(slot=1, expiration=expiration)

print("Item ID:", item.id)
print("API key (slot 1):", result["access_token"])

# state.json is written by the scripts, unlike .env. It doesn't hold the key: deploy that to your app
# state.json: {"itemId": "a1f3c9e27b8d4e6f9c0b2d4e6f8a1c3e", "slot": 1}
with open("state.json", "w") as f:
    json.dump({"itemId": item.id, "slot": 1}, f, indent=2)
# #endregion generate