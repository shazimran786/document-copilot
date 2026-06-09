import { Loader2 } from "lucide-react"
import { Link, useOutletContext, useParams } from "react-router-dom"
import { useEffect, useState } from "react"

import { ChatPanel } from "@/components/chat/ChatPanel"
import { ChatErrorBanner } from "@/components/chat/ChatErrorBanner"
import { getThreadMessages } from "@/lib/api"
import type { ChatMessage } from "@/lib/chat-types"
import { ApiError } from "@/lib/http"

type ChatOutletContext = {
  refetchThreads: () => Promise<void>
}

export function ChatPage() {
  const { threadId } = useParams()

  if (!threadId) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-6 py-12 text-center">
        <h2 className="font-heading text-lg font-medium">
          Select or start a conversation
        </h2>
        <p className="mt-2 max-w-md text-sm text-muted-foreground">
          Choose a thread from the sidebar or create a new chat to begin.
        </p>
      </div>
    )
  }

  return <ThreadChatView key={threadId} threadId={threadId} />
}

function ThreadChatView({ threadId }: { threadId: string }) {
  const { refetchThreads } = useOutletContext<ChatOutletContext>()
  const [initialMessages, setInitialMessages] = useState<ChatMessage[]>([])
  const [hydrationKey, setHydrationKey] = useState(0)
  const [hydrationError, setHydrationError] = useState<string | null>(null)
  const [responseTimesByMessageId, setResponseTimesByMessageId] = useState<
    Record<string, number>
  >({})
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<ApiError | null>(null)

  useEffect(() => {
    let cancelled = false

    void (async () => {
      try {
        const messages = await getThreadMessages(threadId)
        if (!cancelled) {
          setInitialMessages(messages)
          setLoading(false)
        }
      } catch (caught) {
        if (!cancelled) {
          setLoadError(
            caught instanceof ApiError
              ? caught
              : new ApiError("Failed to load messages", 0),
          )
          setLoading(false)
        }
      }
    })()

    return () => {
      cancelled = true
    }
  }, [threadId])

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        <Loader2 className="size-6 animate-spin" />
      </div>
    )
  }

  if (loadError) {
    const notFound = loadError.status === 404 || loadError.status === 403
    return (
      <div className="flex flex-1 flex-col justify-center px-6 py-12">
        <ChatErrorBanner
          message={
            notFound
              ? "Conversation not found."
              : loadError.message || "Failed to load this conversation."
          }
        />
        {notFound ? (
          <Link
            to="/chat"
            className="mx-6 mt-3 text-sm text-primary underline-offset-4 hover:underline"
          >
            Back to chat
          </Link>
        ) : null}
      </div>
    )
  }

  async function handleStreamComplete() {
    setHydrationError(null)
    try {
      await refetchThreads()
      const freshMessages = await getThreadMessages(threadId)
      setInitialMessages(freshMessages)
      setHydrationKey((current) => current + 1)
    } catch {
      setHydrationError(
        "Answer saved, but sources could not load. Refresh the page to see citations.",
      )
    }
  }

  return (
    <>
      {hydrationError ? (
        <div className="px-6 pt-3">
          <ChatErrorBanner
            message={hydrationError}
            onRetry={() => void handleStreamComplete()}
          />
        </div>
      ) : null}
      <ChatPanel
        key={`${threadId}-${hydrationKey}`}
        threadId={threadId}
        initialMessages={initialMessages}
        responseTimesByMessageId={responseTimesByMessageId}
        onResponseTimeRecorded={(messageId, elapsedMs) =>
          setResponseTimesByMessageId((current) => ({
            ...current,
            [messageId]: elapsedMs,
          }))
        }
        onStreamComplete={() => void handleStreamComplete()}
      />
    </>
  )
}
