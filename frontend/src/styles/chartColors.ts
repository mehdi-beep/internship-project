// Validated categorical palette (dataviz skill, references/palette.md).
// Fixed hue order — never cycled arbitrarily; slot N always means the same
// hue across every chart in the app so identity stays consistent.
export const CHART_CATEGORICAL: Record<"light" | "dark", string[]> = {
  light: ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"],
  dark: ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
};

// Sequential (single-hue, blue) — for magnitude-only encodings.
export const CHART_SEQUENTIAL_LIGHT = ["#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#1c5cab", "#104281"];

export const CHART_STATUS = {
  good: "#0ca30c",
  warning: "#fab219",
  serious: "#ec835a",
  critical: "#d03b3b",
};

export const CHART_INK = {
  primary: "#0b0b0b",
  secondary: "#52514e",
  muted: "#898781",
  gridline: "#e1e0d9",
  baseline: "#c3c2b7",
};

export function categoricalColor(index: number, mode: "light" | "dark" = "light"): string {
  const palette = CHART_CATEGORICAL[mode];
  return palette[index % palette.length];
}
