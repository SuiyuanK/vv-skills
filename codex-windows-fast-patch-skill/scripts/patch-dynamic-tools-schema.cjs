const fs = require("node:fs");
const path = require("node:path");

const root = process.argv[2];
if (!root) {
  console.error("usage: node patch-dynamic-tools-schema.cjs <asar-extract-root>");
  process.exit(2);
}

const assetsDir = path.join(root, "webview", "assets");
if (!fs.existsSync(assetsDir)) {
  console.error(`assets directory not found: ${assetsDir}`);
  process.exit(2);
}

const files = fs
  .readdirSync(assetsDir)
  .filter((name) => /^app-server-dynamic-tools-.*\.js$/.test(name))
  .map((name) => path.join(assetsDir, name));

if (files.length === 0) {
  console.error("app-server-dynamic-tools asset not found");
  process.exit(2);
}

let patched = 0;
let alreadyPatched = 0;

for (const file of files) {
  const before = fs.readFileSync(file, "utf8");

  if (before.includes("namespace:yr,name:e.name,description:e.description,inputSchema:e.inputSchema")) {
    alreadyPatched += 1;
    continue;
  }

  const repairMissingBrace = "inputSchema:e.inputSchema,...br.has(e.name)?{}:{deferLoading:!0}}))async function Sr";
  if (before.includes(repairMissingBrace)) {
    const repaired = before.replace(
      repairMissingBrace,
      "inputSchema:e.inputSchema,...br.has(e.name)?{}:{deferLoading:!0}}))}async function Sr",
    );
    fs.writeFileSync(file, repaired);
    patched += 1;
    continue;
  }

  const namespaceWrappedTarget =
    "return[{type:`namespace`,name:yr,description:`Tools provided by the Codex app.`,tools:[...h?[x()]:[],...r?.open_in_codex===!0?[ot]:[],T,...h&&C?[y]:[],..._?[dt,...d?[mt(f)]:[]]:[],...g?Jn({availableHandoffHosts:e,availableModels:w,crossHostHandoffEnabled:n}):[],...h&&v?[vt,yt]:[],...m===`conversational_onboarding`?[Pe]:[],...b&&m!==`conversational_onboarding`?[...p,a]:[]].map(e=>({type:`function`,...e,...br.has(e.name)?{}:{deferLoading:!0}}))}]}";
  const flatDynamicToolReplacement =
    "return[...h?[x()]:[],...r?.open_in_codex===!0?[ot]:[],T,...h&&C?[y]:[],..._?[dt,...d?[mt(f)]:[]]:[],...g?Jn({availableHandoffHosts:e,availableModels:w,crossHostHandoffEnabled:n}):[],...h&&v?[vt,yt]:[],...m===`conversational_onboarding`?[Pe]:[],...b&&m!==`conversational_onboarding`?[...p,a]:[]].map(e=>({namespace:yr,name:e.name,description:e.description,inputSchema:e.inputSchema,...br.has(e.name)?{}:{deferLoading:!0}}))}";

  if (!before.includes(namespaceWrappedTarget)) {
    console.error(`dynamic tools namespace target not found in ${file}`);
    process.exit(2);
  }

  fs.writeFileSync(file, before.replace(namespaceWrappedTarget, flatDynamicToolReplacement));
  patched += 1;
}

console.log(
  JSON.stringify({
    status: patched > 0 ? "patched" : "already-patched",
    patched,
    alreadyPatched,
    files: files.map((file) => path.basename(file)),
  }),
);
