import { useEffect, useRef } from "react"

import { AssistantMessageBubble } from "@/components/chat/AssistantMessageBubble"
import { MessageBubble } from "@/components/chat/MessageBubble"
import { StreamingIndicator } from "@/components/chat/StreamingIndicator"
import type { ChatMessage } from "@/lib/chat-types"

type MessageListProps = {
  messages: ChatMessage[]
  status: "submitted" | "streaming" | "ready" | "error"
  liveElapsedMs?: number
  responseTimesByMessageId?: Record<string, number>
}

export function MessageList({
  messages,
  status,
  liveElapsedMs,
  responseTimesByMessageId = {},
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const isStreaming = status === "streaming" || status === "submitted"
  const lastMessage = messages.at(-1)
  const assistantIsStreaming =
    isStreaming && lastMessage?.role === "assistant"
  const waitingForAssistant =
    status === "submitted" && lastMessage?.role === "user"
  const showIndicator = assistantIsStreaming || waitingForAssistant

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, status])

  return (
    <div className="flex-1 overflow-y-auto px-6 py-4">
      <div className="mx-auto flex max-w-3xl flex-col gap-4">
        {messages.map((message, index) => {
          const isLast = index === messages.length - 1
          const streaming =
            isLast && isStreaming && message.role === "assistant"

          if (message.role === "assistant") {
            return (
              <AssistantMessageBubble
                key={message.id}
                message={message}
                streaming={streaming}
                liveElapsedMs={streaming ? liveElapsedMs : undefined}
                responseTimeMs={responseTimesByMessageId[message.id]}
              />
            )
          }

          return (
            <MessageBubble
              key={message.id}
              message={message}
              streaming={streaming}
            />
          )
        })}
        {showIndicator ? (
          <StreamingIndicator
            elapsedMs={waitingForAssistant ? liveElapsedMs : undefined}
          />
        ) : null}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
