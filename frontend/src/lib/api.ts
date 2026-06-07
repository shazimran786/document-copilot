import { getEnv } from "@/lib/env"
import { apiFetch } from "@/lib/http"

export type CurrentUser = {
  id: string
  email: string
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await apiFetch("/me")
  return response.json() as Promise<CurrentUser>
}

export async function getHealth(): Promise<{ status: string }> {
  const response = await fetch(`${getEnv().apiBaseUrl}/health`)
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`)
  }
  return response.json() as Promise<{ status: string }>
}
