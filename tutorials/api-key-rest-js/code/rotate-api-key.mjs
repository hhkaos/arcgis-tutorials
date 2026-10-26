// Rotate an API key: generate a key in the free slot, deploy it, then invalidate the old one.
// Run: node rotate-api-key.mjs
// #region rotate-imports
// Rotate: import the functions
import { readFile, writeFile } from "node:fs/promises";
import { createInterface } from "node:readline/promises";
import { ApplicationCredentialsManager } from "@esri/arcgis-rest-request";
import { invalidateApiKey, updateApiKey } from "@esri/arcgis-rest-developer-credentials";
// #endregion rotate-imports

// #region rotate-config
// Rotate: start from the key in production
process.loadEnvFile(); // reads .env
const authentication = ApplicationCredentialsManager.fromCredentials({
  clientId: process.env.APP_CLIENT_ID,
  clientSecret: process.env.APP_CLIENT_SECRET,
  portal: process.env.PORTAL,
});

// Item and slot of the key in production, saved by create-api-key.mjs
// state.json: {"itemId": "a1f3c9e27b8d4e6f9c0b2d4e6f8a1c3e", "slot": 1}
const { itemId, slot: currentSlot } = JSON.parse(await readFile("state.json", "utf8"));
// #endregion rotate-config

// #region find-slot
// Find the free slot
const newSlot = currentSlot === 1 ? 2 : 1;
// #endregion find-slot

// #region rotate-generate
// Generate the key in the new slot
const expiration = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // 30 days

const result = await updateApiKey({
  itemId,
  authentication,
  generateToken1: newSlot === 1,
  generateToken2: newSlot === 2,
  apiToken1ExpirationDate: newSlot === 1 ? expiration : undefined,
  apiToken2ExpirationDate: newSlot === 2 ? expiration : undefined,
});

const newKey = newSlot === 1 ? result.accessToken1 : result.accessToken2;
console.log(`New API key (slot ${newSlot}):`, newKey);
// New API key (slot 2): AAPTk3Lm9QzR2vWs8EoYbN4tHc7uJ1xA6dFg_example_pQ5nZwB.AT2_K9pLw4Zd
// #endregion rotate-generate

// #region deploy
// Deploy the new key
const prompt = createInterface({ input: process.stdin, output: process.stdout });
await prompt.question("Deploy the new key, then press Enter to invalidate the old one…");
prompt.close();
// #endregion deploy

// #region invalidate
// Invalidate the old key
const { success } = await invalidateApiKey({ itemId, authentication, apiKey: currentSlot });
console.log(`Old key in slot ${currentSlot} invalidated:`, success);

// The key in production is now in the new slot
await writeFile("state.json", JSON.stringify({ itemId, slot: newSlot }, null, 2));
// #endregion invalidate
