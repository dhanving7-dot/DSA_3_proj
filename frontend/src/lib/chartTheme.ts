// Validated categorical / status palette (dark-surface steps), fixed order —
// never cycled or reassigned per-render. See the project's dataviz guidance.
export const SERIES = {
  blue: "#3987e5",
  orange: "#d95926",
  aqua: "#199e70",
  yellow: "#c98500",
  magenta: "#d55181",
  green: "#008300",
  violet: "#9085e9",
  red: "#e66767",
} as const

export const CATEGORICAL = [
  SERIES.blue,
  SERIES.orange,
  SERIES.aqua,
  SERIES.yellow,
  SERIES.magenta,
  SERIES.violet,
  SERIES.red,
]

export const STATUS = {
  good: "#0ca30c",
  warning: "#fab219",
  serious: "#ec835a",
  critical: "#d03b3b",
} as const

export const CHART_CHROME = {
  surface: "#12121a",
  gridline: "#2c2c2a",
  baseline: "#383835",
  textPrimary: "#ffffff",
  textSecondary: "#c3c2b7",
  textMuted: "#898781",
}

export const SEQUENTIAL_BLUE = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]

// One fixed hue per algorithm (validated against the dark chart surface, all checks pass).
// Color follows the algorithm everywhere it is charted - never its position in a list.
export const ALGORITHM_COLORS: Record<string, string> = {
  KUHN: SERIES.blue,
  HOPCROFT_KARP: SERIES.orange,
  EDMONDS_KARP: SERIES.aqua,
  DINIC: SERIES.yellow,
  FORD_FULKERSON: SERIES.magenta,
  MIN_COST_FLOW: SERIES.violet,
}
