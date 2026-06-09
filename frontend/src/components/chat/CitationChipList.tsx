import { CitationChip } from "@/components/chat/CitationChip"
import type { CitationMetadata } from "@/lib/citations"

type CitationChipListProps = {
  citations: CitationMetadata[]
  selectedChunkId: string | null
  onSelect: (citation: CitationMetadata) => void
}

export function CitationChipList({
  citations,
  selectedChunkId,
  onSelect,
}: CitationChipListProps) {
  if (citations.length === 0) {
    return null
  }

  return (
    <div className="mt-3 space-y-2 border-t border-border/60 pt-3">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        Sources
      </p>
      <div className="flex flex-col gap-2">
        {citations.map((citation, index) => (
          <CitationChip
            key={citation.chunkId}
            citation={citation}
            index={index}
            selected={selectedChunkId === citation.chunkId}
            onSelect={() => onSelect(citation)}
          />
        ))}
      </div>
    </div>
  )
}
