// Hands the committed summary file to the page, after checking it. The page never reads raw trip rows.
import {COMPANIES, countBy, isCount, isNumber, readSummary} from "../../lib/read-summary.js";

process.stdout.write(readSummary("monthly.csv", ({header, rows, fail}) => {
  if (header.join() !== "month,company,days,trips,wait_trips,wait_median_min,wait_p90_min") fail(`unexpected columns: ${header}`);
  const months = countBy(rows, 0);
  if (months.size !== 12) fail(`expected 12 months, found ${months.size}`);
  const companies = countBy(rows, 1);
  for (const c of COMPANIES) if (companies.get(c) !== months.size) fail(`expected one row per month for ${c}`);
  for (const [month, , days, trips, waitTrips, median, p90] of rows) {
    if (!/^\d{4}-\d{2}$/.test(month)) fail(`bad month "${month}"`);
    if (!(Number(days) >= 28 && Number(days) <= 31)) fail(`${month}: ${days} days`);
    if (!isCount(trips) || !isCount(waitTrips)) fail(`${month}: trip counts are not positive whole numbers`);
    if (!isNumber(median) || !isNumber(p90) || Number(median) <= 0 || Number(p90) < Number(median)) fail(`${month}: wait times look wrong`);
  }
}));
