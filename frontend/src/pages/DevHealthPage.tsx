import { useEffect, useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { getCurrentUser, getHealth } from "@/lib/api"
import { ApiError } from "@/lib/http"

type CheckState = "idle" | "loading" | "ok" | "error"

export function DevHealthPage() {
  const [healthState, setHealthState] = useState<CheckState>("loading")
  const [meState, setMeState] = useState<CheckState>("loading")
  const [healthDetail, setHealthDetail] = useState<string>("")
  const [meDetail, setMeDetail] = useState<string>("")
  const [runId, setRunId] = useState(0)

  useEffect(() => {
    let cancelled = false

    void (async () => {
      try {
        const health = await getHealth()
        if (!cancelled) {
          setHealthState("ok")
          setHealthDetail(health.status)
        }
      } catch (caught) {
        if (!cancelled) {
          setHealthState("error")
          setHealthDetail(
            caught instanceof Error ? caught.message : "Health check failed",
          )
        }
      }

      try {
        const user = await getCurrentUser()
        if (!cancelled) {
          setMeState("ok")
          setMeDetail(`${user.email} (${user.id})`)
        }
      } catch (caught) {
        if (!cancelled) {
          setMeState("error")
          setMeDetail(
            caught instanceof ApiError
              ? caught.message
              : caught instanceof Error
                ? caught.message
                : "Authenticated request failed",
          )
        }
      }
    })()

    return () => {
      cancelled = true
    }
  }, [runId])

  function rerunChecks() {
    setHealthState("loading")
    setMeState("loading")
    setHealthDetail("")
    setMeDetail("")
    setRunId((current) => current + 1)
  }

  return (
    <div className="flex flex-1 items-center justify-center px-6 py-12">
      <Card className="w-full max-w-xl">
        <CardHeader>
          <CardTitle>Dev diagnostics</CardTitle>
          <CardDescription>
            Confirms the browser session reaches the FastAPI backend with your
            Supabase bearer token.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <StatusRow label="GET /health" state={healthState} detail={healthDetail} />
          <StatusRow label="GET /me" state={meState} detail={meDetail} />
          <Button variant="outline" onClick={rerunChecks}>
            Re-run checks
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

function StatusRow({
  label,
  state,
  detail,
}: {
  label: string
  state: CheckState
  detail: string
}) {
  const statusLabel =
    state === "loading"
      ? "Checking…"
      : state === "ok"
        ? "OK"
        : state === "error"
          ? "Failed"
          : "Pending"

  return (
    <div className="rounded-lg border border-border px-4 py-3">
      <div className="flex items-center justify-between gap-3">
        <p className="font-medium">{label}</p>
        <span className="text-sm text-muted-foreground">{statusLabel}</span>
      </div>
      {detail ? <p className="mt-2 text-sm text-muted-foreground">{detail}</p> : null}
    </div>
  )
}
