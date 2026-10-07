// Hands the committed summary file to the page, after checking it. The page never reads raw trip rows.
import {COMPANIES, countBy, isNumber, readSummary} from "../../lib/read-summary.js";

process.stdout.write(readSummary("heatmap.csv", ({header, rows, fail}) => {
  if (header.join() !== "company,weekday,hour,avg_trips") fail(`unexpected columns: ${header}`);
  const companies = countBy(rows, 0);
  for (const c of COMPANIES) if (companies.get(c) !== 7 * 24) fail(`expected 168 weekday and hour slots for ${c}, found ${companies.get(c) ?? 0}`);
  for (const [company, weekday, hour, trips] of rows) {
    if (!(weekday >= 1 && weekday <= 7) || !(hour >= 0 && hour <= 23)) fail(`${company}: bad slot ${weekday} ${hour}`);
    if (!isNumber(trips) || Number(trips) < 0) fail(`${company} ${weekday} ${hour}: bad trip count "${trips}"`);
  }
}));
