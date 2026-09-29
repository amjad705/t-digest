// Renders BOTH T Digest formats — the Letter-size broadsheet (format 1) and
// the A4 country-briefing (format 2) — to PDF via headless Chrome.
// No email step: delivery is handled separately (e.g. WhatsApp).
//
// Usage:
//   node t_digest_dual_render.js \
//     --html1 "C:\Users\User\Desktop\claude data\T Digest.html" \
//     --out1 "T Digest - Broadsheet - 2026-07-14.pdf" \
//     --html2 "C:\Users\User\Desktop\claude data\T Digest - Briefing.html" \
//     --out2 "T Digest - Briefing - 2026-07-14.pdf"

const path = require("path");
const puppeteer = require("puppeteer-core");

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

// CSS-px page widths (96 dpi) for the formats page.pdf() supports here.
const PAGE_WIDTH_IN = { Letter: 8.5, A4: 8.2677165354 };

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

async function renderPdf(htmlPath, outPath, format, margin) {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
  });
  const page = await browser.newPage();
  // Both templates' print CSS drops max-width, so .sheet/.page fills the
  // actual print content width — narrower than any screen-mode viewport.
  // page.pdf() reflows at that content width (page width minus margins)
  // regardless of the viewport used for the preceding evaluate/measure pass,
  // so the viewport must match it exactly. Otherwise the in-page autofit
  // script sizes for the wrong width and its fitted content can overflow
  // onto extra pages once the real print reflow happens.
  const marginIn = parseFloat(margin.left);
  const contentWidthPx = Math.round((PAGE_WIDTH_IN[format] - 2 * marginIn) * 96);
  await page.setViewport({ width: contentWidthPx, height: 2000, deviceScaleFactor: 1 });
  await page.emulateMediaType("print");
  await page.goto("file:///" + path.resolve(htmlPath).replace(/\\/g, "/"), {
    waitUntil: "networkidle0",
  });
  await page.pdf({
    path: outPath,
    format,
    printBackground: true,
    margin,
  });
  await browser.close();
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const required = ["html1", "out1", "html2", "out2"];
  for (const key of required) {
    if (!args[key]) {
      console.error(`Missing required --${key} argument`);
      process.exit(1);
    }
  }

  await renderPdf(args.html1, args.out1, "Letter", { top: "0.6in", bottom: "0.6in", left: "0.6in", right: "0.6in" });
  console.log(`Wrote ${args.out1}`);

  await renderPdf(args.html2, args.out2, "A4", { top: "0.55in", bottom: "0.55in", left: "0.55in", right: "0.55in" });
  console.log(`Wrote ${args.out2}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
