import type { UIMessage } from "ai"

export type ChatThread = {
  id: string
  title: string
  createdAt: string
  updatedAt: string
}

export type CitationMetadata = {
  chunkId: string
  stableChunkId: string
  claimIndex: number
  excerpt: string
  passageText?: string
  ticker: string
  companyName: string
  filingType: string
  fiscalYear: number
  sectionLabel: string | null
  pageLabel: string | null
  sourceUrl: string
  accessionNumber: string
}

export type AssistantMessageMetadata = {
  citations: CitationMetadata[]
  insufficientEvidence: boolean
  validationFailed: boolean
}

export type ChatMessage = UIMessage & {
  metadata?: AssistantMessageMetadata
}
