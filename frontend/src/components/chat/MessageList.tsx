import { useEffect, useRef } from "react"

import { MessageBubble } from "@/components/chat/MessageBubble"
import { StreamingIndicator } from "@/components/chat/StreamingIndicator"
import type { ChatMessage } from "@/lib/chat-types"

type MessageListProps = {
  messages: ChatMessage[]
  status: "submitted" | "streaming" | "ready" | "error"
}

export function MessageList({ messages, status }: MessageListProps) {
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

          return (
            <MessageBubble
              key={message.id}
              message={message}
              streaming={streaming}
            />
          )
        })}
        {showIndicator ? <StreamingIndicator /> : null}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
