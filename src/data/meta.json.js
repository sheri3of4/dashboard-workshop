// Which TLC files the summaries came from and when TLC published them, checked before use.
import {readFileSync} from "node:fs";

const text = readFileSync(new URL("../../data/summaries/meta.json", import.meta.url), "utf8");
const meta = JSON.parse(text);
const isDate = (d) => /^\d{4}-\d{2}-\d{2}$/.test(d);
if (!isDate(meta.latest_published) || meta.sources?.length !== 12 || !meta.sources.every((s) => isDate(s.published))) {
  throw new Error("meta.json failed its checks: expected 12 sources with publish dates. Re-run the pipeline.");
}
process.stdout.write(text);
