import { formatResponseDuration } from "@/lib/format-duration"

type ResponseTimeLabelProps = {
  elapsedMs: number
  streaming?: boolean
}

export function ResponseTimeLabel({
  elapsedMs,
  streaming = false,
}: ResponseTimeLabelProps) {
  const label = streaming
    ? formatResponseDuration(elapsedMs)
    : `Responded in ${formatResponseDuration(elapsedMs)}`

  return (
    <p
      className="mt-1.5 text-xs tabular-nums text-muted-foreground"
      aria-live={streaming ? "polite" : "off"}
      aria-label={label}
    >
      {label}
    </p>
  )
}
