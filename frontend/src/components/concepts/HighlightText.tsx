/** Shows `text` with every [start, start + length) occurrence highlighted (overlaps merge). */
export function HighlightText({ text, positions, length, maxChars = 1200 }: { text: string; positions: number[]; length: number; maxChars?: number }) {
  const shown = text.slice(0, maxChars)
  const covered = new Array<boolean>(shown.length).fill(false)
  for (const p of positions) {
    for (let i = p; i < Math.min(p + length, shown.length); i++) covered[i] = true
  }
  const parts: { text: string; hit: boolean }[] = []
  for (let i = 0; i < shown.length; i++) {
    const last = parts[parts.length - 1]
    if (last && last.hit === covered[i]) last.text += shown[i]
    else parts.push({ text: shown[i], hit: covered[i] })
  }
  return (
    <p className="max-h-48 overflow-auto whitespace-pre-wrap break-all rounded-lg border border-border-subtle bg-white/[0.02] p-3 font-mono text-xs leading-relaxed text-ink-secondary">
      {parts.map((part, i) =>
        part.hit ? (
          <mark key={i} className="rounded-sm bg-brand-500/35 px-0.5 text-ink">
            {part.text}
          </mark>
        ) : (
          <span key={i}>{part.text}</span>
        )
      )}
      {text.length > maxChars && <span className="text-ink-muted"> … ({text.length - maxChars} more characters)</span>}
    </p>
  )
}

/** Highlight explicit [start, end) spans inside a short value (used by entity search results). */
export function HighlightSpans({ value, spans }: { value: string; spans: [number, number][] }) {
  if (!spans.length) return <>{value}</>
  const positions = spans.map(([s]) => s)
  const length = spans[0][1] - spans[0][0]
  const covered = new Array<boolean>(value.length).fill(false)
  for (const p of positions) for (let i = p; i < Math.min(p + length, value.length); i++) covered[i] = true
  const out: { t: string; h: boolean }[] = []
  for (let i = 0; i < value.length; i++) {
    const last = out[out.length - 1]
    if (last && last.h === covered[i]) last.t += value[i]
    else out.push({ t: value[i], h: covered[i] })
  }
  return (
    <>
      {out.map((o, i) =>
        o.h ? (
          <mark key={i} className="rounded-sm bg-brand-500/35 text-ink">
            {o.t}
          </mark>
        ) : (
          <span key={i}>{o.t}</span>
        )
      )}
    </>
  )
}
