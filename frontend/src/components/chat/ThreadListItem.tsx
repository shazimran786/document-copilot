type ThreadListItemProps = {
  id: string
  title: string
  updatedAt: string
  active: boolean
  onSelect: (id: string) => void
}

function formatRelativeTime(iso: string): string {
  const date = new Date(iso)
  const diffSeconds = Math.round((date.getTime() - Date.now()) / 1000)
  const absSeconds = Math.abs(diffSeconds)
  const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" })

  if (absSeconds < 60) {
    return rtf.format(diffSeconds, "second")
  }

  const diffMinutes = Math.round(diffSeconds / 60)
  if (Math.abs(diffMinutes) < 60) {
    return rtf.format(diffMinutes, "minute")
  }

  const diffHours = Math.round(diffMinutes / 60)
  if (Math.abs(diffHours) < 24) {
    return rtf.format(diffHours, "hour")
  }

  const diffDays = Math.round(diffHours / 24)
  if (Math.abs(diffDays) < 7) {
    return rtf.format(diffDays, "day")
  }

  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  })
}

export function ThreadListItem({
  id,
  title,
  updatedAt,
  active,
  onSelect,
}: ThreadListItemProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(id)}
      className={`w-full rounded-lg px-3 py-2 text-left transition-colors ${
        active
          ? "bg-muted text-foreground"
          : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
      }`}
    >
      <p className="truncate text-sm font-medium">{title}</p>
      <p className="mt-0.5 text-xs text-muted-foreground">
        {formatRelativeTime(updatedAt)}
      </p>
    </button>
  )
}
