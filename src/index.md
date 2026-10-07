---
title: Operations overview
---

```js
// Exact versions, so every build uses the same chart code. The downloaded copies are committed
// in src/.observablehq/cache/_npm/. To upgrade: change a version here, delete that folder,
// run npm run build, look at the page, then commit.
import * as Plot from "npm:@observablehq/plot@0.6.17";
import * as d3 from "npm:d3@7.9.0";
```

```js
const monthly = FileAttachment("data/monthly.csv").csv({typed: true});
const heatmap = FileAttachment("data/heatmap.csv").csv({typed: true});
const zones = FileAttachment("data/zones.csv").csv({typed: true});
const meta = FileAttachment("data/meta.json").json();
```

```js
// Colors come from the design system tokens. Reading `dark` re-runs this when the theme
// changes, so the charts follow light and dark mode.
const colors = (dark, (() => {
  const style = getComputedStyle(document.documentElement);
  const token = (name) => style.getPropertyValue(name).trim();
  return {
    Uber: token("--color-series-1"),
    Lyft: token("--color-series-2"),
    accent: token("--color-accent"),
    text: token("--color-text"),
    muted: token("--color-text-muted"),
    surface: token("--color-surface")
  };
})());
```

```js
const formatInt = d3.format(",.0f");
const formatPct = d3.format("+.1%");
const formatMin = d3.format(".1f");
const formatMonth = d3.utcFormat("%B %Y");
const formatMonthShort = d3.utcFormat("%B");
// A change in minutes, or "No change" when it rounds to zero.
const formatMinChange = (x) => (Math.abs(x) < 0.05 ? "No change" : `${d3.format("+.1f")(x)} min`);
const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

// Zone 264 is "Unknown" and 265 is "Outside of NYC". Neither is a place anyone can act on,
// so both are left out of the zone rankings.
const notAPlace = new Set([264, 265]);
const zoneLabel = (d) => `${d.zone} (${d.borough})`;
```

# NYC rideshare operations

<p class="fine-print">High volume for-hire trips (Uber and Lyft) in New York City, ${formatMonth(monthly[0].month)} to ${formatMonth(monthly.at(-1).month)}. Figures cover every trip in the period. Newest TLC file published ${d3.utcFormat("%-d %B %Y")(new Date(meta.latest_published))}.</p>

```js
const company = view(Inputs.radio(["All", "Uber", "Lyft"], {label: "Company", value: "All"}));
```

```js
const selected = monthly.filter((d) => d.company === company);
const last = selected.at(-1);
const prev = selected.at(-2);
const perDay = (d) => d.trips / d.days;
const seriesColor = company === "All" ? colors.accent : colors[company];
const daysInPeriod = d3.sum(selected, (d) => d.days);
```

<h2>${formatMonth(last.month)} at a glance</h2>

<div class="grid grid-cols-3">
  <div class="card">
    <h2>Trips per day</h2>
    <div class="big">${formatInt(perDay(last))}</div>
    <div class="change">${formatPct(perDay(last) / perDay(prev) - 1)} vs ${formatMonthShort(prev.month)}</div>
  </div>
  <div class="card">
    <h2>Median wait</h2>
    <div class="big">${formatMin(last.wait_median_min)} min</div>
    <div class="change">${formatMinChange(last.wait_median_min - prev.wait_median_min)} vs ${formatMonthShort(prev.month)}</div>
  </div>
  <div class="card">
    <h2>1 in 10 riders wait longer than</h2>
    <div class="big">${formatMin(last.wait_p90_min)} min</div>
    <div class="change">${formatMinChange(last.wait_p90_min - prev.wait_p90_min)} vs ${formatMonthShort(prev.month)}</div>
  </div>
</div>

## Are trips up or down?

```js
const volume = company === "All" ? monthly.filter((d) => d.company !== "All") : selected;
```

<div class="card">
  ${resize((width) => Plot.plot({
    width,
    height: 300,
    marginRight: 50,
    y: {grid: true, label: "Trips per day", tickFormat: "s", zero: true},
    x: {label: null, type: "utc"},
    color: {domain: ["Uber", "Lyft"], range: [colors.Uber, colors.Lyft], legend: company === "All"},
    marks: [
      Plot.ruleY([0]),
      Plot.lineY(volume, {x: "month", y: perDay, stroke: "company", strokeWidth: 2}),
      Plot.dot(volume, {x: "month", y: perDay, fill: "company", r: 3}),
      Plot.text(volume, Plot.selectLast({x: "month", y: perDay, z: "company", text: "company", dx: 8, textAnchor: "start", fill: colors.text})),
      Plot.tip(volume, Plot.pointerX({x: "month", y: perDay, z: "company", title: (d) => `${d.company}, ${formatMonth(d.month)}\n${formatInt(perDay(d))} trips per day\n${formatInt(d.trips)} trips in the month`}))
    ]
  }))}
</div>

## When and where is demand highest?

<div class="grid grid-cols-2">
  <div class="card">
    <h2>Average trips by weekday and hour</h2>
    ${resize((width) => Plot.plot({
      width,
      height: 260,
      marginLeft: 40,
      padding: 0,
      x: {label: "Hour of day", tickFormat: (h) => (h % 3 === 0 ? String(h) : "")},
      y: {label: null, tickFormat: (d) => weekdays[d - 1]},
      color: {type: "linear", range: [colors.surface, seriesColor], legend: true, label: "Average trips in that hour", tickFormat: "s"},
      marks: [
        Plot.cell(heatmap.filter((d) => d.company === company), {
          x: "hour", y: "weekday", fill: "avg_trips", inset: 1, rx: 2,
          tip: true,
          title: (d) => `${weekdays[d.weekday - 1]}, ${d.hour}:00 to ${d.hour + 1}:00\n${formatInt(d.avg_trips)} trips on average`
        })
      ]
    }))}
  </div>
  <div class="card">
    <h2>Busiest pickup zones, trips per day</h2>
    ${resize((width) => Plot.plot({
      width,
      height: 260,
      marginLeft: Math.min(230, width * 0.45),
      x: {grid: true, label: null, tickFormat: "s"},
      y: {label: null},
      marks: [
        Plot.barX(busiest, {x: (d) => d.trips / daysInPeriod, y: zoneLabel, fill: seriesColor, sort: {y: "-x"}, rx: 2, insetTop: 2, insetBottom: 2, tip: true,
          title: (d) => `${zoneLabel(d)}\n${formatInt(d.trips / daysInPeriod)} trips per day\n${formatInt(d.trips)} trips in the year`}),
        Plot.ruleX([0])
      ]
    }))}
  </div>
</div>

```js
const zonesForCompany = zones.filter((d) => d.company === company && !notAPlace.has(d.zone_id));
const busiest = d3.sort(zonesForCompany, (d) => -d.trips).slice(0, 10);
const minTrips = 10000;
const longestWaits = d3.sort(zonesForCompany.filter((d) => d.trips >= minTrips), (d) => -d.wait_p90_min).slice(0, 10);
```

## How long are riders waiting, and where is it worst?

<div class="grid grid-cols-2">
  <div class="card">
    <h2>Wait from request to pickup, minutes</h2>
    ${resize((width) => Plot.plot({
      width,
      height: 260,
      marginRight: 110,
      y: {grid: true, label: null, zero: true},
      x: {label: null, type: "utc"},
      marks: [
        Plot.ruleY([0]),
        Plot.lineY(selected, {x: "month", y: "wait_p90_min", stroke: colors.text, strokeWidth: 2}),
        Plot.lineY(selected, {x: "month", y: "wait_median_min", stroke: colors.muted, strokeWidth: 2, strokeDasharray: "4,3"}),
        Plot.text(selected, Plot.selectLast({x: "month", y: "wait_p90_min", text: () => "1 in 10 wait longer", dx: 8, textAnchor: "start", fill: colors.text})),
        Plot.text(selected, Plot.selectLast({x: "month", y: "wait_median_min", text: () => "Median", dx: 8, textAnchor: "start", fill: colors.muted})),
        Plot.tip(selected, Plot.pointerX({x: "month", y: "wait_p90_min", title: (d) => `${formatMonth(d.month)}\nMedian ${formatMin(d.wait_median_min)} min\n1 in 10 wait longer than ${formatMin(d.wait_p90_min)} min`}))
      ]
    }))}
  </div>
  <div class="card">
    <h2>Zones where 1 in 10 riders wait longest, minutes</h2>
    ${resize((width) => Plot.plot({
      width,
      height: 260,
      marginLeft: Math.min(230, width * 0.45),
      marginRight: 40,
      x: {grid: true, label: null},
      y: {label: null},
      marks: [
        Plot.barX(longestWaits, {x: "wait_p90_min", y: zoneLabel, fill: seriesColor, sort: {y: "-x"}, rx: 2, insetTop: 2, insetBottom: 2, tip: true,
          title: (d) => `${zoneLabel(d)}\n1 in 10 wait longer than ${formatMin(d.wait_p90_min)} min\nMedian ${formatMin(d.wait_median_min)} min\n${formatInt(d.trips)} trips in the year`}),
        Plot.text(longestWaits, {x: "wait_p90_min", y: zoneLabel, text: (d) => formatMin(d.wait_p90_min), dx: 6, textAnchor: "start", fill: colors.text}),
        Plot.ruleX([0])
      ]
    }))}
  </div>
</div>

<p class="fine-print">Wait is the time from the ride request to pickup, over the full year for the zone rankings. Zones with fewer than ${formatInt(minTrips)} trips in the year are left out of the wait ranking, so a handful of trips cannot top it. ${formatInt(d3.sum(selected, (d) => d.trips - d.wait_trips))} trips (${d3.format(".1%")(d3.sum(selected, (d) => d.trips - d.wait_trips) / d3.sum(selected, (d) => d.trips))}) are left out of wait times because the pickup is recorded before the request or more than an hour after it.</p>

<details>
  <summary>Zone figures as a table</summary>

```js
Inputs.table(zonesForCompany, {
  columns: ["zone", "borough", "trips", "wait_median_min", "wait_p90_min"],
  header: {zone: "Zone", borough: "Borough", trips: "Trips in the year", wait_median_min: "Median wait (min)", wait_p90_min: "1 in 10 wait longer than (min)"},
  sort: "trips",
  reverse: true
})
```

</details>

<p class="fine-print">The trip records are submitted to TLC by the companies. TLC states it cannot confirm their accuracy or completeness. Company names come from TLC's licence numbers: HV0003 is Uber and HV0005 is Lyft.</p>
