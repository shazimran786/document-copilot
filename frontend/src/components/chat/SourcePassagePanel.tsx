import { ExternalLink, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { formatCitationLabel, type CitationMetadata } from "@/lib/citations"

type SourcePassagePanelProps = {
  citation: CitationMetadata
  onClose: () => void
}

export function SourcePassagePanel({
  citation,
  onClose,
}: SourcePassagePanelProps) {
  const passageText = citation.passageText ?? citation.excerpt

  return (
    <Card className="mt-3 border-primary/20 bg-background shadow-sm">
      <CardHeader className="border-b">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <CardTitle className="text-sm">
              {formatCitationLabel(citation)}
            </CardTitle>
            <CardDescription className="text-xs">
              {citation.ticker} · {citation.accessionNumber}
            </CardDescription>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label="Close source passage"
            onClick={onClose}
          >
            <X />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-4">
        <div>
          <p className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Grounded excerpt
          </p>
          <blockquote className="rounded-md border-l-4 border-primary/40 bg-muted/40 px-3 py-2 text-sm italic">
            {citation.excerpt}
          </blockquote>
        </div>
        <div>
          <p className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Full passage
          </p>
          <div className="max-h-64 overflow-y-auto rounded-md bg-muted/30 p-3 text-sm leading-relaxed whitespace-pre-wrap">
            {passageText}
          </div>
        </div>
        <a
          href={citation.sourceUrl}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-sm text-primary underline-offset-4 hover:underline"
        >
          View on SEC EDGAR
          <ExternalLink className="size-3.5" aria-hidden />
        </a>
      </CardContent>
    </Card>
  )
}
