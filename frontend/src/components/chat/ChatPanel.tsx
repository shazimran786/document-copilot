import { useChat } from "@ai-sdk/react"
import { DefaultChatTransport } from "ai"
import { useCallback } from "react"

import { ChatComposer } from "@/components/chat/ChatComposer"
import { ChatErrorBanner } from "@/components/chat/ChatErrorBanner"
import { MessageList } from "@/components/chat/MessageList"
import type { ChatMessage } from "@/lib/chat-types"
import { getEnv } from "@/lib/env"
import { getAccessToken } from "@/lib/supabase"

type ChatPanelProps = {
  threadId: string
  initialMessages: ChatMessage[]
  onStreamComplete?: () => void
}

export function ChatPanel({
  threadId,
  initialMessages,
  onStreamComplete,
}: ChatPanelProps) {
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

  const handleSubmit = useCallback(
    (text: string) => {
      clearError()
      void sendMessage({ text })
    },
    [clearError, sendMessage],
  )

  const isBusy = status === "streaming" || status === "submitted"
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
            Document Copilot will search curated 10-K filings once ingestion
            and retrieval are connected. For now, you will receive a stubbed
            reply to verify the chat flow.
          </p>
        </div>
      ) : (
        <MessageList messages={messages} status={status} />
      )}

      <ChatComposer
        disabled={isBusy}
        onSubmit={handleSubmit}
        autoFocus={showEmptyState}
      />
    </div>
  )
}
