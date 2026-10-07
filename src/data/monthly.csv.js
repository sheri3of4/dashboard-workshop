// Hands the committed summary file to the page. The page never reads raw trip rows.
import {readFileSync} from "node:fs";

process.stdout.write(readFileSync(new URL("../../data/summaries/monthly.csv", import.meta.url)));
