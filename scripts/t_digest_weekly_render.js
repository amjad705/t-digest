// Renders the T Digest Weekly Summary (A4, 1 page) to PDF via headless Chrome.
//
// Usage:
//   node t_digest_weekly_render.js \
//     --html "C:\Users\User\Desktop\claude data\T Digest - Weekly Summary.html" \
//     --out "T Digest - Weekly Summary - 2026-07-13-to-2026-07-19.pdf"

const path = require("path");
const puppeteer = require("puppeteer-core");

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

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

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
  });
  const page = await browser.newPage();
  await page.goto("file:///" + path.resolve(args.html).replace(/\\/g, "/"), {
    waitUntil: "networkidle0",
  });
  await page.pdf({
    path: args.out,
    format: "A4",
    printBackground: true,
    margin: { top: "0.5in", bottom: "0.5in", left: "0.5in", right: "0.5in" },
  });
  await browser.close();
  console.log(`Wrote ${args.out}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
