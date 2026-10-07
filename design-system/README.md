# Design system

A small, neutral style guide for this starter. It is meant to be followed
by default, whether a person or an agent is building the dashboard.

## How to use it

Import `tokens.css` once, at the top of your stylesheet or app entry point.
Use the CSS custom properties it defines (`var(--color-text)`,
`var(--font-sans)`, and so on) everywhere. Never hardcode a color, a font
name, or a hex value in a component; if you need a value that is not a
token yet, add a token for it here instead of writing it inline.

## Ask before styling anything

Before writing any CSS, ask the person you are building this for: does
your company already have a style guide, brand colors, fonts, or a logo
you want used instead of the defaults below? Ask this once, at the start,
and move on either way.

- If they have brand assets, replace the tokens in `tokens.css` and the
  file in `logo.svg` with theirs, and say plainly what you changed and why.
- If they do not have one, or do not know, use the defaults in this guide
  and do not ask again.

## Typography

Two typefaces, both free on Google Fonts:

- **Inter** for interface text: titles, labels, body copy.
- **JetBrains Mono** for code, table values, and numbers.

Type scale:

| Use | Token |
|---|---|
| Page title | `--text-page-title` |
| Section title | `--text-section-title` |
| Body | `--text-body` |
| Small print | `--text-small` |

Numbers in tables and charts should use tabular figures so digits line up
in a column. Add the `.tabular-nums` class from `tokens.css`, or set
`font-variant-numeric: tabular-nums` directly.

## Color

Each palette defines the same set of tokens: page background, surface
(cards and panels), border, text, muted text, one accent, and three status
colors.

### Light palette (default)

| Token | Hex |
|---|---|
| `--color-background` | `#ffffff` |
| `--color-surface` | `#f4f5f7` |
| `--color-border` | `#d8dbe0` |
| `--color-text` | `#1a1d21` |
| `--color-text-muted` | `#5b6169` |
| `--color-accent` | `#0f766e` |
| `--color-success` | `#15803d` |
| `--color-warning` | `#b45309` |
| `--color-error` | `#b91c1c` |

### Dark palette

| Token | Hex |
|---|---|
| `--color-background` | `#14161a` |
| `--color-surface` | `#1d2025` |
| `--color-border` | `#33373d` |
| `--color-text` | `#eceef1` |
| `--color-text-muted` | `#9aa0a8` |
| `--color-accent` | `#2dd4bf` |
| `--color-success` | `#4ade80` |
| `--color-warning` | `#fbbf24` |
| `--color-error` | `#f87171` |

**Contrast rule:** body text must read at 4.5:1 or better against its
background. `--color-text` and `--color-text-muted` were checked against
`--color-background` and `--color-surface` in both palettes and clear that
bar; the accent and the three status colors were checked against their own
palette's background too, since they are also used to label short text.
Nothing here is navy paired with cyan; the accent is a single teal, muted
on light backgrounds and lightened for dark ones so it stays legible in
both directions.

### Chart series

Two colors for telling series apart in a chart, such as one line per company. They are
separate from the accent and the status colors, so a series never reads as a warning.
Both pairs were run through a colorblind separation and contrast check against their own
background.

| Token | Light | Dark |
|---|---|---|
| `--color-series-1` | `#0d9488` | `#0fa596` |
| `--color-series-2` | `#eb6834` | `#d95926` |

Always pair series colors with a legend or a direct label, never color alone.

## Dark mode

The dark palette applies automatically, following the operating system,
through a `prefers-color-scheme: dark` media query in `tokens.css`. If you
want a manual toggle as well, set `data-theme="dark"` or `data-theme="light"`
on `<html>`. Each one wins over the device setting, so a theme picker works
in both directions; remove the attribute to follow the device again.

```css
/* From tokens.css: automatic, system-driven dark mode */
@media (prefers-color-scheme: dark) {
  :root {
    --color-background: #14161a;
    --color-text: #eceef1;
    --color-accent: #2dd4bf;
    /* ...and the rest of the dark palette */
  }
}
```

Components should only ever read the token, never the palette directly, so
this switch needs no changes anywhere else.

## Controls

Filters need four controls: a text box, a dropdown, a radio group, and a
checkbox. Build each one from the tokens defined above (border, surface,
text, accent); never introduce a bespoke color for a control or its states.

**Labels.** Every control needs a visible label, placed above it or beside
it. Placeholder text is not a label: it disappears once someone starts
typing, and screen readers do not treat it as one.

**Sizing.** All four controls share one height, `--control-height`, so a
row of filters lines up. On small screens, raise the touch target to at
least 44 pixels tall; anything shorter is hard to tap accurately.

**Focus.** Every control shows a visible focus ring in the accent color
when it receives keyboard focus. Never set `outline: none` without
supplying a replacement ring; a control that swallows focus without
showing it is unusable by keyboard.

**Disabled.** A disabled control is faded and does not accept input; its
label stays legible.

**Invalid.** An invalid control gets a border in the error color, paired
with visible error text near the label, not color alone.

```html
<div class="field">
  <label for="region">Region</label>
  <select id="region">
    <option>All</option>
    <option>North</option>
  </select>
</div>
```

## Logo

`logo.svg` is a placeholder mark: three simple bars, drawn in a neutral
gray so it reads on both light and dark backgrounds. It stands in for a
real logo until one is supplied. Place it at the top left of the page,
next to or above the page title, sized around 32 to 48 pixels tall.

## Icons

Use [Lucide](https://lucide.dev) icons. Stick to the outline style, one
stroke weight throughout, and size each icon to match the text sitting
next to it, usually 16 to 20 pixels for inline use. Do not use an icon by
itself where a short label would be clearer; pair them.

A basic dashboard typically needs:

- `refresh-cw` for reloading data
- `filter` for opening filter controls
- `download` for exporting a table or chart
- `info` for a note or tooltip

## Do and do not

- Do use the tokens for every color and font; do not write a hex value or
  a font name directly in a component.
- Do ask about brand assets once, at the start, before styling anything.
- Do check new text colors against their background before using them.
- Do not pair the accent with itself for both a link and a status color;
  keep success, warning, and error distinct from the accent.
- Do not add new tokens without a reason; keep the palette small.
