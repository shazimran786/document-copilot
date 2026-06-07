import { getEnv } from "@/lib/env"
import { getAccessToken } from "@/lib/supabase"

export class ApiError extends Error {
  readonly status: number
  readonly body: unknown

  constructor(message: string, status: number, body: unknown = undefined) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.body = body
  }
}

type ApiFetchOptions = RequestInit & {
  auth?: boolean
}

export async function apiFetch(
  path: string,
  options: ApiFetchOptions = {},
): Promise<Response> {
  const { auth = true, headers: initHeaders, ...init } = options
  const headers = new Headers(initHeaders)

  if (auth) {
    const token = await getAccessToken()
    if (!token) {
      throw new ApiError("Not authenticated", 401)
    }
    headers.set("Authorization", `Bearer ${token}`)
  }

  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }

  const response = await fetch(`${getEnv().apiBaseUrl}${path}`, {
    ...init,
    headers,
  })

  if (!response.ok) {
    let body: unknown
    try {
      body = await response.json()
    } catch {
      body = undefined
    }

    const detail =
      typeof body === "object" &&
      body !== null &&
      "detail" in body &&
      typeof body.detail === "string"
        ? body.detail
        : `Request failed with status ${response.status}`

    throw new ApiError(detail, response.status, body)
  }

  return response
}
