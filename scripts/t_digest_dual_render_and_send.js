// Renders BOTH T Digest formats — the Letter-size broadsheet (format 1) and
// the A4 country-briefing (format 2) — to PDF via headless Chrome, then
// emails both as attachments in a single message via Gmail SMTP.
//
// Usage:
//   node t_digest_dual_render_and_send.js \
//     --html1 "C:\Users\User\Desktop\claude data\T Digest.html" \
//     --out1 "T Digest - Broadsheet - 2026-07-12.pdf" \
//     --html2 "C:\Users\User\Desktop\claude data\T Digest - Briefing.html" \
//     --out2 "T Digest - Briefing - 2026-07-12.pdf" \
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

async function renderPdf(htmlPath, outPath, format, margin) {
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
    format,
    printBackground: true,
    margin,
  });
  await browser.close();
}

async function sendEmail({ to, from, passwordFile, outPaths, subject, text }) {
  const password = fs.readFileSync(passwordFile, "utf8").trim();
  const transporter = nodemailer.createTransport({
    service: "gmail",
    auth: { user: from, pass: password },
  });
  await transporter.sendMail({
    from,
    to,
    subject: subject || `T Digest — ${new Date().toISOString().slice(0, 10)}`,
    text: text || "Attached: today's T Digest in both formats — the broadsheet edition and the country-briefing edition.",
    attachments: outPaths.map((p) => ({ filename: path.basename(p), path: p })),
  });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const required = ["html1", "out1", "html2", "out2", "to", "from", "password-file"];
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

  await sendEmail({
    to: args.to,
    from: args.from,
    passwordFile: args["password-file"],
    outPaths: [args.out1, args.out2],
    subject: args.subject,
    text: args.text,
  });
  console.log(`Emailed both T Digest formats to ${args.to}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
