// Authenticate a backend script with OAuth credentials (app authentication).
// Run: node app-auth.mjs
// #region imports
// Import the functions
import { ApplicationCredentialsManager, request } from "@esri/arcgis-rest-request";
// #endregion imports

// #region config
// Configure the script
const settings = {
  clientId: "<client_id>", // @var client_id
  clientSecret: "<client_secret>", // @var client_secret
  portalUrl: "www.arcgis.com", // @var portal_url
};
// #endregion config

// #region sign-in
// Sign in as the application
const authentication = ApplicationCredentialsManager.fromCredentials({
  clientId: settings.clientId,
  clientSecret: settings.clientSecret,
  portal: `https://${settings.portalUrl}/sharing/rest`,
});
// #endregion sign-in

// #region token
// Request a token
const token = await authentication.getToken();
console.log("Access token:", token);
console.log("Expires:", authentication.expires.toISOString());
// #endregion token

// #region request
// Make a request
const portalInfo = await request(`${authentication.portal}/portals/self`, {
  authentication,
});

console.log(`Title: "${portalInfo.appinfo.appTitle}"`);
console.log("Has the following privileges:");
for (const privilege of portalInfo.appinfo.privileges) {
  console.log(`\t- ${privilege}`);
}
// #endregion request
