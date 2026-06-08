import { useCallback, useEffect, useState } from "react"

import { createThread as apiCreateThread, listThreads } from "@/lib/api"
import type { ChatThread } from "@/lib/chat-types"
import { ApiError } from "@/lib/http"

type UseThreadsResult = {
  threads: ChatThread[]
  loading: boolean
  error: ApiError | null
  creating: boolean
  refetch: () => Promise<void>
  createThread: (title?: string) => Promise<ChatThread>
}

export function useThreads(): UseThreadsResult {
  const [threads, setThreads] = useState<ChatThread[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)

  const refetch = useCallback(async () => {
    try {
      const nextThreads = await listThreads()
      setThreads(nextThreads)
      setError(null)
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught
          : new ApiError("Failed to load conversations", 0),
      )
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    void (async () => {
      setLoading(true)
      try {
        const nextThreads = await listThreads()
        if (!cancelled) {
          setThreads(nextThreads)
          setError(null)
        }
      } catch (caught) {
        if (!cancelled) {
          setError(
            caught instanceof ApiError
              ? caught
              : new ApiError("Failed to load conversations", 0),
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    })()

    return () => {
      cancelled = true
    }
  }, [])

  const createThread = useCallback(async (title?: string) => {
    setCreating(true)
    try {
      const thread = await apiCreateThread(title)
      setThreads((current) => [thread, ...current])
      setError(null)
      return thread
    } catch (caught) {
      const nextError =
        caught instanceof ApiError
          ? caught
          : new ApiError("Failed to create conversation", 0)
      setError(nextError)
      throw nextError
    } finally {
      setCreating(false)
    }
  }, [])

  return {
    threads,
    loading,
    error,
    creating,
    refetch,
    createThread,
  }
}
