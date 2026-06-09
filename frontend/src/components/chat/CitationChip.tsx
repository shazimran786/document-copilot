import { ExternalLink } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  formatCitationAriaLabel,
  formatCitationLabel,
  type CitationMetadata,
} from "@/lib/citations"

type CitationChipProps = {
  citation: CitationMetadata
  index: number
  selected: boolean
  onSelect: () => void
}

export function CitationChip({
  citation,
  index,
  selected,
  onSelect,
}: CitationChipProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button
        type="button"
        variant={selected ? "default" : "outline"}
        size="sm"
        className="h-auto max-w-full whitespace-normal py-1.5 text-left"
        aria-label={formatCitationAriaLabel(citation, index)}
        aria-pressed={selected}
        onClick={onSelect}
      >
        <span className="mr-1 font-medium text-muted-foreground">
          [{index + 1}]
        </span>
        {formatCitationLabel(citation)}
      </Button>
      <a
        href={citation.sourceUrl}
        target="_blank"
        rel="noreferrer"
        className="inline-flex items-center gap-1 text-xs text-primary underline-offset-4 hover:underline"
        aria-label={`View ${citation.companyName} filing on SEC EDGAR`}
      >
        SEC
        <ExternalLink className="size-3" aria-hidden />
      </a>
    </div>
  )
}
