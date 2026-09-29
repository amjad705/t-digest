// Renders T Digest — a single-flow Letter-size document (.sheet div, with
// internal `break-before:page` dividers, 0.6in margins) — to a
// pixel-perfect PDF via headless Chrome, then emails it via Gmail SMTP with
// the PDF attached.
//
// Usage:
//   node t_digest_render_and_send.js \
//     --html "C:\Users\User\.claude\T Digest.html" \
//     --out "T Digest - 2026-07-12.pdf" \
//     --to <YOUR_EMAIL> \
//     --from <YOUR_EMAIL> \
//     --password-file "C:\Users\User\.claude\secrets\war-report-gmail-app-password.txt"

const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer-core");
const nodemailer = require("nodemailer");

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

async function renderPdf(htmlPath, outPath) {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
  });
  const page = await browser.newPage();
  await page.goto("file:///" + path.resolve(htmlPath).replace(/\\/g, "/"), {
    waitUntil: "networkidle0",
  });
  await page.pdf({
    path: outPath,
    format: "Letter",
    printBackground: true,
    margin: { top: "0.6in", bottom: "0.6in", left: "0.6in", right: "0.6in" },
  });
  await browser.close();
}

async function sendEmail({ to, from, passwordFile, outPath, subject, text }) {
  const password = fs.readFileSync(passwordFile, "utf8").trim();
  const transporter = nodemailer.createTransport({
    service: "gmail",
    auth: { user: from, pass: password },
  });
  await transporter.sendMail({
    from,
    to,
    subject: subject || `T Digest — ${new Date().toISOString().slice(0, 10)}`,
    text: text || "Attached: today's T Digest — India, Pakistan & Global security-technology briefing (2 pages, A4).",
    attachments: [{ filename: path.basename(outPath), path: outPath }],
  });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const required = ["html", "out", "to", "from", "password-file"];
  for (const key of required) {
    if (!args[key]) {
      console.error(`Missing required --${key} argument`);
      process.exit(1);
    }
  }

  await renderPdf(args.html, args.out);
  console.log(`Wrote ${args.out}`);

  await sendEmail({
    to: args.to,
    from: args.from,
    passwordFile: args["password-file"],
    outPath: args.out,
    subject: args.subject,
    text: args.text,
  });
  console.log(`Emailed T Digest to ${args.to}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
