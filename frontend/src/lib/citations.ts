import type {
  AssistantMessageMetadata,
  ChatMessage,
  CitationMetadata,
} from "@/lib/chat-types"

export type { AssistantMessageMetadata, CitationMetadata }

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null
}

function parseCitationMetadata(value: unknown): CitationMetadata | null {
  if (!isRecord(value)) {
    return null
  }

  const {
    chunkId,
    stableChunkId,
    claimIndex,
    excerpt,
    passageText,
    ticker,
    companyName,
    filingType,
    fiscalYear,
    sectionLabel,
    pageLabel,
    sourceUrl,
    accessionNumber,
  } = value

  if (
    typeof chunkId !== "string" ||
    typeof stableChunkId !== "string" ||
    typeof claimIndex !== "number" ||
    typeof excerpt !== "string" ||
    typeof ticker !== "string" ||
    typeof companyName !== "string" ||
    typeof filingType !== "string" ||
    typeof fiscalYear !== "number" ||
    typeof sourceUrl !== "string" ||
    typeof accessionNumber !== "string"
  ) {
    return null
  }

  return {
    chunkId,
    stableChunkId,
    claimIndex,
    excerpt,
    passageText: typeof passageText === "string" ? passageText : undefined,
    ticker,
    companyName,
    filingType,
    fiscalYear,
    sectionLabel: typeof sectionLabel === "string" ? sectionLabel : null,
    pageLabel: typeof pageLabel === "string" ? pageLabel : null,
    sourceUrl,
    accessionNumber,
  }
}

export function getAssistantMetadata(
  message: ChatMessage,
): AssistantMessageMetadata | null {
  if (message.role !== "assistant") {
    return null
  }

  const metadata = (message as ChatMessage & { metadata?: unknown }).metadata
  if (!isRecord(metadata)) {
    return null
  }

  const rawCitations = metadata.citations
  const citations = Array.isArray(rawCitations)
    ? rawCitations
        .map(parseCitationMetadata)
        .filter((citation): citation is CitationMetadata => citation !== null)
        .sort((left, right) => left.claimIndex - right.claimIndex)
    : []

  return {
    citations,
    insufficientEvidence: metadata.insufficientEvidence === true,
    validationFailed: metadata.validationFailed === true,
  }
}

export function formatCitationLabel(citation: CitationMetadata): string {
  const section = citation.sectionLabel ?? "Section not specified"
  const page = citation.pageLabel ? ` · p. ${citation.pageLabel}` : ""
  return `${citation.companyName} · ${citation.filingType} FY${citation.fiscalYear} · ${section}${page}`
}

export function formatCitationAriaLabel(
  citation: CitationMetadata,
  index: number,
): string {
  return `Citation ${index + 1}: ${formatCitationLabel(citation)}`
}
