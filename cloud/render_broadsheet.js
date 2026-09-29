// Cloud version of t_digest_dual_render.js (Broadsheet only): renders
// cloud/T Digest.html to a Letter-size PDF using the Chromium installed in
// Claude Code cloud sessions instead of the Windows Chrome path.
//
// Usage (from the repo root, after `npm ci --prefix scripts`):
//   node cloud/render_broadsheet.js --html "cloud/T Digest.html" --out "T Digest - Broadsheet - YYYY-MM-DD.pdf"

const path = require("path");
const puppeteer = require(path.join(__dirname, "..", "scripts", "node_modules", "puppeteer-core"));

const CHROME_PATH = process.env.CHROME_PATH || "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const MARGIN_IN = 0.6;

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith("--")) {
      args[argv[i].slice(2)] = argv[i + 1];
      i++;
    }
  }
  return args;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  for (const key of ["html", "out"]) {
    if (!args[key]) {
      console.error(`Missing required --${key} argument`);
      process.exit(1);
    }
  }
  const browser = await puppeteer.launch({ executablePath: CHROME_PATH, headless: true, args: ["--no-sandbox"] });
  const page = await browser.newPage();
  // Match the print content width so the in-page autofit sizes correctly.
  await page.setViewport({ width: Math.round((8.5 - 2 * MARGIN_IN) * 96), height: 2000, deviceScaleFactor: 1 });
  await page.emulateMediaType("print");
  await page.goto("file://" + path.resolve(args.html), { waitUntil: "networkidle0" });
  const m = MARGIN_IN + "in";
  await page.pdf({ path: args.out, format: "Letter", printBackground: true, margin: { top: m, bottom: m, left: m, right: m } });
  await browser.close();
  console.log(`Wrote ${args.out}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
