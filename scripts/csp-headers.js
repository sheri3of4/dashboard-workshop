// Writes dist/_headers with a Content-Security-Policy that allows exactly the inline scripts
// Framework put in the built pages. Those scripts change on every build, so their hashes are
// computed here after the build rather than written into netlify.toml.
import {createHash} from "node:crypto";
import {readdirSync, readFileSync, writeFileSync} from "node:fs";
import {join} from "node:path";
import {fileURLToPath} from "node:url";

const dist = fileURLToPath(new URL("../dist/", import.meta.url));
const hashes = new Set();
for (const file of readdirSync(dist, {recursive: true})) {
  if (!file.endsWith(".html")) continue;
  const html = readFileSync(join(dist, file), "utf8");
  for (const [, body] of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)) {
    if (body.trim()) hashes.add(`'sha256-${createHash("sha256").update(body).digest("base64")}'`);
  }
}
if (hashes.size === 0) throw new Error("No inline scripts found in dist/; did the build run?");

const csp = [
  "default-src 'self'",
  // d3-dsv, which reads the CSV files, builds its row parser with new Function, so 'unsafe-eval' is required.
  `script-src 'self' ${[...hashes].join(" ")} 'unsafe-eval'`,
  // Plot adds a <style> element to each chart, so inline styles are required.
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "font-src https://fonts.gstatic.com",
  "img-src 'self' data:",
  "connect-src 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'none'",
  "frame-ancestors 'none'"
].join("; ");

writeFileSync(join(dist, "_headers"), `/*\n  Content-Security-Policy: ${csp}\n`);
console.log(`Wrote dist/_headers (${hashes.size} inline script hash${hashes.size === 1 ? "" : "es"})`);
