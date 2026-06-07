import { Navigate } from "react-router-dom"

import { useSession } from "@/hooks/useSession"

type PublicRouteProps = {
  children: React.ReactNode
}

export function PublicRoute({ children }: PublicRouteProps) {
  const { session, loading } = useSession()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
        Loading session…
      </div>
    )
  }

  if (session) {
    return <Navigate to="/" replace />
  }

  return children
}
