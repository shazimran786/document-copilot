import { useState } from "react"
import { Send } from "lucide-react"

import { Button } from "@/components/ui/button"

type ChatComposerProps = {
  disabled?: boolean
  onSubmit: (text: string) => void
  autoFocus?: boolean
}

export function ChatComposer({
  disabled,
  onSubmit,
  autoFocus,
}: ChatComposerProps) {
  const [input, setInput] = useState("")

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const text = input.trim()
    if (!text || disabled) {
      return
    }
    onSubmit(text)
    setInput("")
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      handleSubmit(event)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-border bg-background px-6 py-4"
    >
      <div className="mx-auto flex max-w-3xl items-end gap-2">
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about SEC filings…"
          rows={1}
          autoFocus={autoFocus}
          disabled={disabled}
          className="max-h-40 min-h-10 flex-1 resize-none rounded-lg border border-input bg-background px-3 py-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50"
        />
        <Button
          type="submit"
          size="icon"
          disabled={disabled || !input.trim()}
          aria-label="Send message"
        >
          <Send />
        </Button>
      </div>
    </form>
  )
}
