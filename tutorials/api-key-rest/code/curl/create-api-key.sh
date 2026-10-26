#!/usr/bin/env bash
# Create API key credentials and generate the first API key (slot 1).
# Requires curl and jq.

# Print each response when VERBOSE=1. They include secrets: don't enable it where logs are kept
log() {
  local response
  response=$(cat)
  if [ -n "$VERBOSE" ]; then jq . <<<"$response" >&2; fi
  printf '%s\n' "$response"
}

# #region sign-in
# Sign in
source .env
TOKEN=$(curl -s -X POST "$PORTAL/oauth2/token" \
  -d client_id="$APP_CLIENT_ID" \
  -d client_secret="$APP_CLIENT_SECRET" \
  -d grant_type=client_credentials \
  -d f=json | log | jq -r .access_token)
# #endregion sign-in

# #region add-item
# Create the credential item
# Portal wizard › Item details: title, tags and description
ITEM_ID=$(curl -s -X POST "$PORTAL/content/users/$ITEM_OWNER/addItem" \
  -d type=Application \
  --data-urlencode title="My API key credentials tutorial" \
  --data-urlencode tags="api key,basemaps,geocoding" \
  --data-urlencode snippet="Key for the store locator app" \
  -d token="$TOKEN" \
  -d f=json | log | jq -r .id)
# #endregion add-item

# #region register
# Register the item as an app
# Portal wizard › Privileges: services the key can call (+ portal:app:access:item:<id> per item)
PRIVILEGES="premium:user:basemaps,premium:user:geocode" # @var privileges

# Portal wizard › Settings: httpReferrers empty = any site can use the key. Set your app's URL(s) before you ship
APP=$(curl -s -X POST "$PORTAL/oauth2/registerApp" \
  -d itemId="$ITEM_ID" \
  -d appType=multiple \
  --data-urlencode 'redirect_uris=["urn:ietf:wg:oauth:2.0:oob"]' \
  --data-urlencode "privileges=$(jq -cn --arg p "$PRIVILEGES" '$p | split(",") | map(gsub("^ +| +$"; ""))')" \
  --data-urlencode 'httpReferrers=[]' \
  -d token="$TOKEN" \
  -d f=json | log)
CLIENT_ID=$(echo "$APP" | jq -r .client_id)
CLIENT_SECRET=$(echo "$APP" | jq -r .client_secret)
# #endregion register

# #region expiration
# Set the expiration of slot 1
# Portal wizard › Settings: expiration date (max. 1 year)
EXPIRES=$(( ($(date +%s) + 30 * 86400) * 1000 )) # 30 days from now, epoch ms
curl -s -X POST "$PORTAL/content/users/$ITEM_OWNER/items/$ITEM_ID/update" \
  -d apiToken1ExpirationDate="$EXPIRES" \
  -d token="$TOKEN" \
  -d f=json | log >/dev/null
# #endregion expiration

# #region generate
# Generate the API key
# Portal wizard › Generate API key: generate the key in slot 1 now
API_KEY=$(curl -s -X POST "$PORTAL/oauth2/token" \
  -d client_id="$CLIENT_ID" \
  -d client_secret="$CLIENT_SECRET" \
  -d grant_type=client_credentials \
  -d apiToken=1 \
  -d regenerateApiToken=false \
  -d f=json | log | jq -r .access_token)

echo "Item ID: $ITEM_ID"
echo "API key (slot 1): $API_KEY"

# state.json is written by the scripts, unlike .env. It doesn't hold the key: deploy that to your app
# state.json: {"itemId": "a1f3c9e27b8d4e6f9c0b2d4e6f8a1c3e", "slot": 1}
jq -n --arg id "$ITEM_ID" '{itemId: $id, slot: 1}' > state.json
# #endregion generate
