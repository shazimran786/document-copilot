import { AlertCircle } from "lucide-react"

import { Button } from "@/components/ui/button"

type ChatErrorBannerProps = {
  message: string
  onRetry?: () => void
}

export function ChatErrorBanner({ message, onRetry }: ChatErrorBannerProps) {
  return (
    <div className="mx-6 mb-3 flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
      <AlertCircle className="mt-0.5 size-4 shrink-0" />
      <div className="flex flex-1 flex-wrap items-center justify-between gap-3">
        <p>{message}</p>
        {onRetry ? (
          <Button variant="outline" size="sm" onClick={onRetry}>
            Try again
          </Button>
        ) : null}
      </div>
    </div>
  )
}
