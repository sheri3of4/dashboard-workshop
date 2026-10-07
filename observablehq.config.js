import {readFileSync} from "node:fs";

// The logo lives in the design system; inline it so there is one copy of the file.
const logo = readFileSync(new URL("./design-system/logo.svg", import.meta.url), "utf8");

export default {
  title: "NYC Rideshare Operations",
  root: "src",
  style: "style.css",
  head: `<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap">`,
  header: `<div class="site-header"><span class="site-logo" aria-hidden="true">${logo}</span><span>NYC Rideshare Operations</span></div>`,
  footer: "Source: NYC Taxi and Limousine Commission trip record data.",
  sidebar: false,
  pager: false,
  toc: false,
  search: false
};
