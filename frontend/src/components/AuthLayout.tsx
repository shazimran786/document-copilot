import { Link, useLocation } from "react-router-dom"

import { cn } from "@/lib/utils"

type AuthLayoutProps = {
  title: string
  description: string
  children: React.ReactNode
}

export function AuthLayout({ title, description, children }: AuthLayoutProps) {
  const { pathname } = useLocation()
  const isSignUp = pathname === "/signup"

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 px-4">
      <div className="w-full max-w-md space-y-4">
        <div className="grid grid-cols-2 gap-1 rounded-lg bg-muted p-1">
          <Link
            to="/login"
            className={cn(
              "rounded-md px-3 py-2 text-center text-sm font-medium transition-colors",
              !isSignUp
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            Sign in
          </Link>
          <Link
            to="/signup"
            className={cn(
              "rounded-md px-3 py-2 text-center text-sm font-medium transition-colors",
              isSignUp
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            Sign up
          </Link>
        </div>

        <div className="rounded-xl bg-card p-6 ring-1 ring-foreground/10">
          <div className="mb-6 space-y-1">
            <h1 className="font-heading text-xl font-medium">{title}</h1>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>
          {children}
        </div>
      </div>
    </div>
  )
}
