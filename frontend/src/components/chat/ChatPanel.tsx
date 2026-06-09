import { useChat } from "@ai-sdk/react"
import { DefaultChatTransport } from "ai"
import { useCallback, useEffect, useRef, useState } from "react"

import { ChatComposer } from "@/components/chat/ChatComposer"
import { ChatErrorBanner } from "@/components/chat/ChatErrorBanner"
import { MessageList } from "@/components/chat/MessageList"
import type { ChatMessage } from "@/lib/chat-types"
import { getEnv } from "@/lib/env"
import { getAccessToken } from "@/lib/supabase"

type ChatPanelProps = {
  threadId: string
  initialMessages: ChatMessage[]
  responseTimesByMessageId?: Record<string, number>
  onResponseTimeRecorded?: (messageId: string, elapsedMs: number) => void
  onStreamComplete?: () => void
}

export function ChatPanel({
  threadId,
  initialMessages,
  responseTimesByMessageId = {},
  onResponseTimeRecorded,
  onStreamComplete,
}: ChatPanelProps) {
  const streamStartedAtRef = useRef<number | null>(null)
  const recordedStreamRef = useRef(false)
  const [liveElapsedMs, setLiveElapsedMs] = useState(0)

  const { messages, sendMessage, status, error, clearError } = useChat({
    id: threadId,
    messages: initialMessages,
    transport: new DefaultChatTransport({
      api: `${getEnv().apiBaseUrl}/chat/stream`,
      headers: async () => {
        const token = await getAccessToken()
        if (!token) {
          throw new Error("Not authenticated")
        }
        return {
          Authorization: `Bearer ${token}`,
        }
      },
      prepareSendMessagesRequest: ({ id, messages: chatMessages }) => ({
        body: {
          threadId: id,
          messages: chatMessages,
        },
      }),
    }),
    onFinish: () => {
      onStreamComplete?.()
    },
  })

  const isBusy = status === "streaming" || status === "submitted"

  useEffect(() => {
    if (
      status !== "ready" ||
      streamStartedAtRef.current === null ||
      recordedStreamRef.current
    ) {
      return
    }

    const elapsedMs = Date.now() - streamStartedAtRef.current
    const lastAssistant = [...messages]
      .reverse()
      .find((message) => message.role === "assistant")
    if (lastAssistant && onResponseTimeRecorded) {
      onResponseTimeRecorded(lastAssistant.id, elapsedMs)
    }
    recordedStreamRef.current = true
    streamStartedAtRef.current = null
  }, [status, messages, onResponseTimeRecorded])

  useEffect(() => {
    const streamingOrSubmitted =
      status === "streaming" || status === "submitted"
    if (!streamingOrSubmitted || streamStartedAtRef.current === null) {
      return
    }

    const tick = () => {
      setLiveElapsedMs(Date.now() - (streamStartedAtRef.current ?? Date.now()))
    }
    tick()
    const intervalId = window.setInterval(tick, 100)
    return () => window.clearInterval(intervalId)
  }, [status])

  const handleSubmit = useCallback(
    (text: string) => {
      clearError()
      streamStartedAtRef.current = Date.now()
      recordedStreamRef.current = false
      setLiveElapsedMs(0)
      void sendMessage({ text })
    },
    [clearError, sendMessage],
  )

  const showEmptyState = messages.length === 0 && status === "ready"

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {error ? (
        <ChatErrorBanner
          message={error.message || "Something went wrong. Please try again."}
          onRetry={clearError}
        />
      ) : null}

      {showEmptyState ? (
        <div className="flex flex-1 flex-col items-center justify-center px-6 py-12 text-center">
          <h2 className="font-heading text-lg font-medium">
            Ask a question about SEC filings
          </h2>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">
            Search curated 10-K filings for Apple, Microsoft, NVIDIA, Amazon,
            and Alphabet (2021–2025). Answers cite the source filing so you
            can verify each claim in one click.
          </p>
        </div>
      ) : (
        <MessageList
          messages={messages}
          status={status}
          liveElapsedMs={isBusy ? liveElapsedMs : undefined}
          responseTimesByMessageId={responseTimesByMessageId}
        />
      )}

      <ChatComposer
        disabled={isBusy}
        onSubmit={handleSubmit}
        autoFocus={showEmptyState}
      />
    </div>
  )
}
