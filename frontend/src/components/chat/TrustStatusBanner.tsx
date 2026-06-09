import { AlertTriangle, Info } from "lucide-react"

type TrustStatusBannerProps = {
  insufficientEvidence: boolean
  validationFailed: boolean
}

export function TrustStatusBanner({
  insufficientEvidence,
  validationFailed,
}: TrustStatusBannerProps) {
  if (validationFailed) {
    return (
      <div
        className="flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-950 dark:text-amber-100"
        role="status"
      >
        <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
        <p>
          Could not verify citations for this answer against the retrieved
          filings. Try rephrasing or asking about a narrower topic.
        </p>
      </div>
    )
  }

  if (insufficientEvidence) {
    return (
      <div
        className="flex items-start gap-2 rounded-lg border border-sky-500/30 bg-sky-500/10 px-3 py-2 text-sm text-sky-950 dark:text-sky-100"
        role="status"
      >
        <Info className="mt-0.5 size-4 shrink-0" aria-hidden />
        <p>
          Not enough evidence in the curated filings to answer this confidently.
          The bot will not infer beyond what is in the corpus.
        </p>
      </div>
    )
  }

  return null
}
