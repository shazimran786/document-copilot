import { isTextUIPart } from "ai"
import { useState } from "react"

import { CitationChipList } from "@/components/chat/CitationChipList"
import { ResponseTimeLabel } from "@/components/chat/ResponseTimeLabel"
import { SourcePassagePanel } from "@/components/chat/SourcePassagePanel"
import { TrustStatusBanner } from "@/components/chat/TrustStatusBanner"
import type { ChatMessage } from "@/lib/chat-types"
import {
  getAssistantMetadata,
  type CitationMetadata,
} from "@/lib/citations"

type AssistantMessageBubbleProps = {
  message: ChatMessage
  streaming?: boolean
  liveElapsedMs?: number
  responseTimeMs?: number
}

function getMessageText(message: ChatMessage): string {
  return message.parts
    .filter(isTextUIPart)
    .map((part) => part.text)
    .join("")
}

export function AssistantMessageBubble({
  message,
  streaming,
  liveElapsedMs,
  responseTimeMs,
}: AssistantMessageBubbleProps) {
  const text = getMessageText(message)
  const metadata = getAssistantMetadata(message)
  const [selectedCitation, setSelectedCitation] =
    useState<CitationMetadata | null>(null)

  if (!text && !streaming) {
    return null
  }

  const showTrustBanner =
    metadata?.insufficientEvidence || metadata?.validationFailed

  const showLiveTime =
    streaming && liveElapsedMs !== undefined && liveElapsedMs > 0
  const showFinalTime =
    !streaming && responseTimeMs !== undefined && responseTimeMs > 0

  return (
    <div className="flex flex-col items-start">
      <div className="max-w-[85%] rounded-2xl bg-muted px-4 py-2.5 text-sm leading-relaxed text-foreground">
        {text || (streaming ? "\u00a0" : null)}

        {!streaming && metadata ? (
          <>
            {showTrustBanner ? (
              <div className="mt-3">
                <TrustStatusBanner
                  insufficientEvidence={metadata.insufficientEvidence}
                  validationFailed={metadata.validationFailed}
                />
              </div>
            ) : null}

            <CitationChipList
              citations={metadata.citations}
              selectedChunkId={selectedCitation?.chunkId ?? null}
              onSelect={(citation) =>
                setSelectedCitation((current) =>
                  current?.chunkId === citation.chunkId ? null : citation,
                )
              }
            />

            {selectedCitation ? (
              <SourcePassagePanel
                citation={selectedCitation}
                onClose={() => setSelectedCitation(null)}
              />
            ) : null}
          </>
        ) : null}
      </div>
      {showLiveTime ? (
        <ResponseTimeLabel elapsedMs={liveElapsedMs} streaming />
      ) : null}
      {showFinalTime ? (
        <ResponseTimeLabel elapsedMs={responseTimeMs} />
      ) : null}
    </div>
  )
}
