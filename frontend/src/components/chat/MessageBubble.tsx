import { isTextUIPart } from "ai"

import type { ChatMessage } from "@/lib/chat-types"

type MessageBubbleProps = {
  message: ChatMessage
  streaming?: boolean
}

function getMessageText(message: ChatMessage): string {
  return message.parts
    .filter(isTextUIPart)
    .map((part) => part.text)
    .join("")
}

export function MessageBubble({ message, streaming }: MessageBubbleProps) {
  const isUser = message.role === "user"
  const text = getMessageText(message)

  if (!text && !streaming) {
    return null
  }

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-foreground"
        }`}
      >
        {text || (streaming ? "\u00a0" : null)}
      </div>
    </div>
  )
}
