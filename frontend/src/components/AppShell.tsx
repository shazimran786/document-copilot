import { LogOut, MessageSquarePlus } from "lucide-react"
import { Outlet } from "react-router-dom"

import { Button } from "@/components/ui/button"
import { useSession } from "@/hooks/useSession"

export function AppShell() {
  const { user, signOut } = useSession()

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <aside className="flex w-72 shrink-0 flex-col border-r border-border">
        <div className="border-b border-border px-4 py-4">
          <p className="font-heading text-base font-medium">Document Copilot</p>
          <p className="text-xs text-muted-foreground">Driftwood Capital</p>
        </div>

        <div className="flex items-center justify-between px-4 py-3">
          <p className="text-sm font-medium">Conversations</p>
          <Button variant="ghost" size="icon-sm" disabled aria-label="New chat">
            <MessageSquarePlus />
          </Button>
        </div>

        <div className="flex-1 px-4 py-2">
          <p className="rounded-lg border border-dashed border-border px-3 py-6 text-center text-sm text-muted-foreground">
            No conversations yet. Chat threads will appear here once the chat API
            is wired up.
          </p>
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

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="border-b border-border px-6 py-4">
          <h1 className="font-heading text-lg font-medium">Chat</h1>
          <p className="text-sm text-muted-foreground">
            Ask questions about SEC filings once ingestion and retrieval are
            connected.
          </p>
        </header>

        <div className="flex flex-1 flex-col items-center justify-center px-6 py-12">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
