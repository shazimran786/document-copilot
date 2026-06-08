import { MessageSquarePlus } from "lucide-react"

import { ThreadListItem } from "@/components/chat/ThreadListItem"
import { Button } from "@/components/ui/button"
import type { ChatThread } from "@/lib/chat-types"

type ThreadListProps = {
  threads: ChatThread[]
  activeThreadId?: string
  loading: boolean
  creating: boolean
  onSelect: (id: string) => void
  onCreate: () => void
}

function ThreadSkeleton() {
  return (
    <div className="space-y-2 px-1">
      {Array.from({ length: 3 }, (_, index) => (
        <div
          key={index}
          className="animate-pulse rounded-lg bg-muted px-3 py-4"
        />
      ))}
    </div>
  )
}

export function ThreadList({
  threads,
  activeThreadId,
  loading,
  creating,
  onSelect,
  onCreate,
}: ThreadListProps) {
  if (loading) {
    return <ThreadSkeleton />
  }

  if (threads.length === 0) {
    return (
      <div className="space-y-3">
        <p className="rounded-lg border border-dashed border-border px-3 py-6 text-center text-sm text-muted-foreground">
          Start your first conversation
        </p>
        <Button className="w-full" onClick={onCreate} disabled={creating}>
          <MessageSquarePlus />
          New chat
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {threads.map((thread) => (
        <ThreadListItem
          key={thread.id}
          id={thread.id}
          title={thread.title}
          updatedAt={thread.updatedAt}
          active={thread.id === activeThreadId}
          onSelect={onSelect}
        />
      ))}
    </div>
  )
}
