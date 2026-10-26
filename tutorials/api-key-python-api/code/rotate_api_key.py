"""Rotate an API key: generate a key in the free slot, deploy it, then invalidate the old one."""
import datetime as dt
import json
import os

from arcgis.gis import GIS
from dotenv import load_dotenv

# #region rotate-config
# Rotate: start from the key in production
load_dotenv()  # reads .env
gis = GIS(
    os.environ["PORTAL_URL"],
    client_id=os.environ["APP_CLIENT_ID"],
    client_secret=os.environ["APP_CLIENT_SECRET"],
)

# Item and slot of the key in production, saved by create_api_key.py
# state.json: {"itemId": "a1f3c9e27b8d4e6f9c0b2d4e6f8a1c3e", "slot": 1}
with open("state.json") as f:
    state = json.load(f)
item = gis.content.get(state["itemId"])
# #endregion rotate-config

# #region find-slot
# Find the free slot
current_slot = state["slot"]
new_slot = 1 if current_slot == 2 else 2
# #endregion find-slot

# #region rotate-generate
# Generate the key in the new slot
expiration = dt.datetime.now() + dt.timedelta(days=30)
item.update(item_properties={f"apiToken{new_slot}ExpirationDate": int(expiration.timestamp() * 1000)})

result = item.generate_api_token(slot=new_slot, regenerate=True, expiration=expiration)
print(f"New API key (slot {new_slot}):", result["access_token"])
# New API key (slot 2): AAPTk3Lm9QzR2vWs8EoYbN4tHc7uJ1xA6dFg_example_pQ5nZwB.AT2_K9pLw4Zd
# #endregion rotate-generate

# #region deploy
# Deploy the new key
input("Deploy the new key, then press Enter to invalidate the old one…")
# #endregion deploy

# #region invalidate
# Invalidate the old key
credential = gis.admin.developer_credentials.get(item.id)
invalidated = credential.revoke(slot=current_slot)
print(f"Old key in slot {current_slot} invalidated:", invalidated)

# The key in production is now in the new slot
with open("state.json", "w") as f:
    json.dump({"itemId": item.id, "slot": new_slot}, f, indent=2)
# #endregion invalidate
