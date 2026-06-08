import { LogOut, MessageSquarePlus } from "lucide-react"
import { Outlet, useNavigate, useParams } from "react-router-dom"

import { ThreadList } from "@/components/chat/ThreadList"
import { Button } from "@/components/ui/button"
import { useSession } from "@/hooks/useSession"
import { useThreads } from "@/hooks/useThreads"

export function AppShell() {
  const { user, signOut } = useSession()
  const { threads, loading, creating, createThread, refetch } = useThreads()
  const { threadId } = useParams()
  const navigate = useNavigate()

  async function handleCreateThread() {
    try {
      const thread = await createThread()
      navigate(`/chat/${thread.id}`)
    } catch {
      // Error state is surfaced via useThreads
    }
  }

  function handleSelectThread(id: string) {
    navigate(`/chat/${id}`)
  }

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <aside className="flex w-72 shrink-0 flex-col border-r border-border">
        <div className="border-b border-border px-4 py-4">
          <p className="font-heading text-base font-medium">Document Copilot</p>
          <p className="text-xs text-muted-foreground">Driftwood Capital</p>
        </div>

        <div className="flex items-center justify-between px-4 py-3">
          <p className="text-sm font-medium">Conversations</p>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="New chat"
            disabled={creating}
            onClick={() => void handleCreateThread()}
          >
            <MessageSquarePlus />
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-2">
          <ThreadList
            threads={threads}
            activeThreadId={threadId}
            loading={loading}
            creating={creating}
            onSelect={handleSelectThread}
            onCreate={() => void handleCreateThread()}
          />
        </div>

        <div className="border-t border-border px-4 py-4">
          <p className="truncate text-sm">{user?.email}</p>
          <Button
            variant="outline"
            size="sm"
            className="mt-3 w-full"
            onClick={() => void signOut()}
          >
            <LogOut />
            Sign out
          </Button>
        </div>
      </aside>

      <main className="flex min-h-screen min-w-0 flex-1 flex-col">
        <header className="shrink-0 border-b border-border px-6 py-4">
          <h1 className="font-heading text-lg font-medium">Chat</h1>
          <p className="text-sm text-muted-foreground">
            Ask questions about SEC filings once ingestion and retrieval are
            connected.
          </p>
        </header>

        <Outlet context={{ refetchThreads: refetch }} />
      </main>
    </div>
  )
}
