// Renders T Daily Digest — a single-flow A4 document (.sheet div, with
// internal `break-before:page` dividers between India / Pakistan / Global) —
// to a pixel-perfect PDF via headless Chrome, then emails it via Gmail SMTP
// with the PDF attached.
//
// Usage:
//   node t_daily_digest_render_and_send.js \
//     --html "C:\Users\User\Desktop\claude data\T Daily Digest.html" \
//     --out "T Daily Digest - 2026-07-12.pdf" \
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
    format: "A4",
    printBackground: true,
    margin: { top: "0", bottom: "0", left: "0", right: "0" },
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
    subject: subject || `T Daily Digest — ${new Date().toISOString().slice(0, 10)}`,
    text: text || "Attached: today's T Daily Digest — India, Pakistan & Global news, A4 PDF.",
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
  console.log(`Emailed T Daily Digest to ${args.to}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
