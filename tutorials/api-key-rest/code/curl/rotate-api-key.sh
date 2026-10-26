#!/usr/bin/env bash
# Rotate an API key: generate a key in the free slot, deploy it, then invalidate the old one.
# Requires curl and jq.

# Print each response when VERBOSE=1. They include secrets: don't enable it where logs are kept
log() {
  local response
  response=$(cat)
  if [ -n "$VERBOSE" ]; then jq . <<<"$response" >&2; fi
  printf '%s\n' "$response"
}

# #region rotate-config
# Rotate: start from the key in production
source .env
# Item and slot of the key in production, saved by create-api-key.sh
# state.json: {"itemId": "a1f3c9e27b8d4e6f9c0b2d4e6f8a1c3e", "slot": 1}
ITEM_ID=$(jq -r .itemId state.json)
CURRENT_SLOT=$(jq -r .slot state.json)
# #endregion rotate-config

# #region app-info
TOKEN=$(curl -s -X POST "$PORTAL/oauth2/token" \
  -d client_id="$APP_CLIENT_ID" \
  -d client_secret="$APP_CLIENT_SECRET" \
  -d grant_type=client_credentials \
  -d f=json | log | jq -r .access_token)

APP=$(curl -s -X POST "$PORTAL/content/users/$ITEM_OWNER/items/$ITEM_ID/registeredAppInfo" \
  -d token="$TOKEN" \
  -d f=json | log)
CLIENT_ID=$(echo "$APP" | jq -r .client_id)
CLIENT_SECRET=$(echo "$APP" | jq -r .client_secret)
# #endregion app-info

# #region find-slot
if [ "$CURRENT_SLOT" = "2" ]; then NEW_SLOT=1; else NEW_SLOT=2; fi
# #endregion find-slot

# #region rotate-expiration
EXPIRES=$(( ($(date +%s) + 30 * 86400) * 1000 )) # 30 days from now, epoch ms
curl -s -X POST "$PORTAL/content/users/$ITEM_OWNER/items/$ITEM_ID/update" \
  -d "apiToken${NEW_SLOT}ExpirationDate=$EXPIRES" \
  -d token="$TOKEN" \
  -d f=json | log >/dev/null
# #endregion rotate-expiration

# #region rotate-generate
NEW_KEY=$(curl -s -X POST "$PORTAL/oauth2/token" \
  -d client_id="$CLIENT_ID" \
  -d client_secret="$CLIENT_SECRET" \
  -d grant_type=client_credentials \
  -d apiToken="$NEW_SLOT" \
  -d regenerateApiToken=true \
  -d f=json | log | jq -r .access_token)
echo "New API key (slot $NEW_SLOT): $NEW_KEY"
# #endregion rotate-generate

# #region deploy
read -r -p "Deploy the new key, then press Enter to invalidate the old one…"
# #endregion deploy

# #region invalidate
SUCCESS=$(curl -s -X POST "$PORTAL/oauth2/revokeToken" \
  -d client_id="$CLIENT_ID" \
  -d client_secret="$CLIENT_SECRET" \
  -d apiToken="$CURRENT_SLOT" \
  -d f=json | log | jq -r .success)
echo "Old key in slot $CURRENT_SLOT invalidated: $SUCCESS"

# The key in production is now in the new slot
jq -n --arg id "$ITEM_ID" --argjson slot "$NEW_SLOT" '{itemId: $id, slot: $slot}' > state.json
# #endregion invalidate
