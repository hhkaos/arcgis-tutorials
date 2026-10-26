// Create API key credentials and generate the first API key (slot 1).
// Run: node create-api-key.mjs
// #region imports
// Import the functions
import { writeFile } from "node:fs/promises";
import { ApplicationCredentialsManager } from "@esri/arcgis-rest-request";
import { createApiKey } from "@esri/arcgis-rest-developer-credentials";
// #endregion imports

// #region sign-in
// Sign in
process.loadEnvFile(); // reads .env
const authentication = ApplicationCredentialsManager.fromCredentials({
  clientId: process.env.APP_CLIENT_ID,
  clientSecret: process.env.APP_CLIENT_SECRET,
  portal: process.env.PORTAL,
});
// #endregion sign-in

// #region create
// Create the credentials
const expiration = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // 30 days

const apiKey = await createApiKey({
  // Portal wizard › Item details
  title: "My API key credentials tutorial",
  description: "Key for the store locator app",
  tags: ["api key", "basemaps", "geocoding"],
  // Portal wizard › Privileges: services the key can call (+ portal:app:access:item:<id> per item)
  privileges: "premium:user:basemaps,premium:user:geocode".split(",").map((p) => p.trim()), // @var privileges
  // Portal wizard › Settings: domains allowed to use the key (empty = any site: set your app's URL before you ship)
  httpReferrers: [],
  // Portal wizard › Settings: expiration (max. 1 year)
  apiToken1ExpirationDate: expiration,
  // Portal wizard › Generate API key: generate the key in slot 1 now
  generateToken1: true,
  authentication,
});
// #endregion create

// #region generate
// Save the key
console.log("Item ID:", apiKey.item.id);
console.log("API key (slot 1):", apiKey.accessToken1);

// state.json is written by the scripts, unlike .env. It doesn't hold the key: deploy that to your app
// state.json: {"itemId": "a1f3c9e27b8d4e6f9c0b2d4e6f8a1c3e", "slot": 1}
await writeFile("state.json", JSON.stringify({ itemId: apiKey.item.id, slot: 1 }, null, 2));
// #endregion generate
