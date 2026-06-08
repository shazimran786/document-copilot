import type { ChatMessage, ChatThread } from "@/lib/chat-types"
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

export async function listThreads(): Promise<ChatThread[]> {
  const response = await apiFetch("/chat/threads")
  return response.json() as Promise<ChatThread[]>
}

export async function createThread(title?: string): Promise<ChatThread> {
  const response = await apiFetch("/chat/threads", {
    method: "POST",
    body: JSON.stringify(title ? { title } : {}),
  })
  return response.json() as Promise<ChatThread>
}

export async function getThreadMessages(threadId: string): Promise<ChatMessage[]> {
  const response = await apiFetch(`/chat/threads/${threadId}/messages`)
  const data = (await response.json()) as { messages: ChatMessage[] }
  return data.messages
}
