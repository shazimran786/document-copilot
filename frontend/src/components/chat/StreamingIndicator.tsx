import { ResponseTimeLabel } from "@/components/chat/ResponseTimeLabel"

type StreamingIndicatorProps = {
  elapsedMs?: number
}

export function StreamingIndicator({ elapsedMs }: StreamingIndicatorProps) {
  return (
    <div className="flex flex-col items-start">
      <div className="flex items-center gap-1 rounded-2xl bg-muted px-4 py-3">
        <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground/70 [animation-delay:0ms]" />
        <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground/70 [animation-delay:150ms]" />
        <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground/70 [animation-delay:300ms]" />
      </div>
      {elapsedMs !== undefined && elapsedMs > 0 ? (
        <ResponseTimeLabel elapsedMs={elapsedMs} streaming />
      ) : null}
    </div>
  )
}
