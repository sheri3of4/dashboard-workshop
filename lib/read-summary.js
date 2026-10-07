// Reads a committed summary file and checks it looks right before the site uses it.
// Data loaders call this; throwing here fails the build, so Netlify keeps the last good site
// live instead of publishing a broken page.
import {readFileSync} from "node:fs";

export const COMPANIES = ["All", "Uber", "Lyft"];

export function readSummary(name, check) {
  const text = readFileSync(new URL(`../data/summaries/${name}`, import.meta.url), "utf8");
  const [header, ...lines] = text.trim().split("\n");
  // Only the first and last columns are read; zone names in the middle may contain commas.
  const rows = lines.map((line) => line.split(","));
  const problems = [];
  check({header: header.split(","), rows, fail: (message) => problems.push(message)});
  if (problems.length) {
    throw new Error(`${name} failed its checks:\n  ${problems.join("\n  ")}\nRe-run the pipeline and look at the file before committing.`);
  }
  return text;
}

export const isCount = (value) => /^\d+$/.test(value) && Number(value) > 0;
export const isNumber = (value) => value !== "" && Number.isFinite(Number(value));

export function countBy(rows, column) {
  const counts = new Map();
  for (const row of rows) counts.set(row[column], (counts.get(row[column]) ?? 0) + 1);
  return counts;
}
