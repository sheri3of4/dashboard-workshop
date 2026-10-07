# Dashboard plan

This is the plan for your dashboard. Fill it in with Claude **before** any code is written,
one section at a time, in plain words. Keep every answer short: a line or two is plenty.
When something changes, change it here first, then build.

Why bother: a dashboard built without a plan is the "vibecoded" kind. It looks finished, nobody
can say whether it is right, and nobody knows what to fix when it breaks. Ten minutes here saves
an afternoon later.

The order follows the engineering process: requirements, a plan with success criteria, build,
test and verify, then maintain.

---

## Who it is for

Name one real person, not "users". Then work backwards from what they are trying to do.
The `jobs-quote-ux` skill is the standard for this section.

- **The person:** a COO overseeing NYC rideshare operations.
- **What they are trying to do:** "Are we growing, where and when is demand, and are riders waiting too long?"
- **How often they look:** weekly, and before the monthly leadership meeting.
- **What they do today instead:** a slide an analyst rebuilds by hand each month.

## The questions it answers

Three to five questions. If a chart does not answer one of these, it does not belong.

| # | Question the person asks | How they will know the answer at a glance |
|---|---|---|
| 1 | Are trips up or down? | Trips per day last month, with the change from the month before; a monthly trend line split by company |
| 2 | When and where is demand highest? | A weekday by hour heatmap of average trips; the busiest pickup zones ranked |
| 3 | How long are riders waiting, and where is it worst? | Median and 90th percentile wait last month, with the change; the zones with the longest waits ranked |

## Data quality checks

Pick the dimensions that matter from the framework you use. If you have none, tell Claude to
use the data quality dimensions in the DAMA-DMBOK. The `/analyze-data-quality` skill walks
through this step.

| Dimension | The rule, in plain words | Where it shows on the dashboard |
|---|---|---|
| _Deferred_ | Operations views come first; quality checks are added later. | |

Found while profiling (12 months, Sep 2025 to Aug 2026, 251,856,731 trips):

- No missing request times, pickup times or pickup zones.
- 1.3% of trips record a pickup before the request. These are left out of wait times, as are
  waits over 60 minutes (0.006%). The page says so next to the wait numbers.
- The source itself carries a caveat: TLC cannot confirm these company-submitted records are
  accurate or complete. The page credits the source and notes this.

## What is on screen

One page, top to bottom:

1. Headline row: trips per day last month, change from the month before, median wait, 90th percentile wait.
2. Volume: trips per day by month, one line per company.
3. Demand: weekday by hour heatmap; top 10 pickup zones.
4. Waits: median and 90th percentile wait by month; the 10 zones with the longest 90th percentile wait
   (zones with at least 10,000 trips a year, so small samples do not dominate).

One filter: company (All, Uber, Lyft). It applies to every section.

Wait time means request to pickup. Companies are named from TLC's licence numbers
(HV0003 is Uber, HV0005 is Lyft).

## Success criteria

How we will know it is done and right. Each one is something we can check, not a feeling.

- [x] Every question in "The questions it answers" is answered on screen
- [x] The headline numbers match the source (spot-check two of them by hand). August 2026 trips per day,
  All (661,080) and Uber (477,421), both match a count straight from the raw file.
- [ ] Every check in "Data quality checks" runs and shows its result
- [ ] Looked at on the live dev site, at the size the person will use it, and it is both correct and pleasing
- [ ] A pass against the ten usability heuristics, with nothing serious left open
- [ ] The security review under "Test and verify" passes
- [ ] _add your own_

## Test and verify

- **Look at it.** Open the live dev site and look at every view, the way the person will. Reading
  the code is not checking. The `closed-loop-visual-feedback` skill covers how.
- **Check the numbers.** Compare the headline numbers against the source.
- **Usability.** Run the `ux-heuristics` skill (Nielsen's ten heuristics) and fix anything serious.
- **Security review.** Ask Claude to review the project as an attacker would, then fix what it finds:
  - [ ] No key or password anywhere in the code or the git history
  - [ ] The browser never receives a key; anything that needs one runs on the server side
  - [ ] Nothing personal or sensitive is sent to the page
  - [ ] Dependencies checked for known problems (`npm audit`)
  - [ ] Who can open the dashboard is a decision you made, not an accident

## Items that will require maintenance

Fill this in as you build: anything that will need attention later, such as a key that
expires or a data source that changes. Include a plan for dependencies that will need to be updated.

- **New months of data.** Copy the new monthly file into `data/raw/`, then run
  `uv run python pipeline/build_summaries.py` and commit the updated `data/summaries/`.
  The page picks up the latest month on its own.
- **Zone names.** `data/reference/taxi_zone_lookup.csv` comes from TLC. If TLC redraws
  zones, download it again and re-run the pipeline.
- **Dependencies.** Observable Framework is pinned in `package.json` and DuckDB in
  `pyproject.toml` (with `uv.lock`). Check for updates every few months with `npm outdated`
  and `uv lock --upgrade`, rebuild, and look at the page before committing.
