// Hands the committed summary file to the page, after checking it. The page never reads raw trip rows.
import {COMPANIES, countBy, isCount, isNumber, readSummary} from "../../lib/read-summary.js";

process.stdout.write(readSummary("zones.csv", ({header, rows, fail}) => {
  if (header.join() !== "company,zone_id,borough,zone,trips,wait_trips,wait_median_min,wait_p90_min") fail(`unexpected columns: ${header}`);
  const companies = countBy(rows, 0);
  for (const c of COMPANIES) if (!((companies.get(c) ?? 0) >= 200)) fail(`expected at least 200 zones for ${c}, found ${companies.get(c) ?? 0}`);
  for (const row of rows) {
    const [company, zoneId] = row;
    const [trips, , median, p90] = row.slice(-4);
    if (!(Number(zoneId) >= 1 && Number(zoneId) <= 265)) fail(`${company}: bad zone id "${zoneId}"`);
    if (!isCount(trips)) fail(`${company} zone ${zoneId}: bad trip count "${trips}"`);
    if (median !== "" && !isNumber(median)) fail(`${company} zone ${zoneId}: bad median wait "${median}"`);
    if (p90 !== "" && !isNumber(p90)) fail(`${company} zone ${zoneId}: bad wait "${p90}"`);
  }
}));
