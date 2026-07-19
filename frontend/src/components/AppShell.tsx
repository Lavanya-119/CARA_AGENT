import type { ReactNode } from "react"
import { Link, useRouterState } from "@tanstack/react-router"
import {
  Home,
  MessageSquare,
  Mic,
  FileText,
  History,
  Settings as SettingsIcon,
  Moon,
  Sun,
  Sparkles,
  LogOut,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useTheme } from "@/hooks/useTheme"
import { useSettings } from "@/hooks/useSettings"

const NAV_ITEMS = [
  { to: "/home", label: "Home", icon: Home },
  { to: "/chat", label: "Chat", icon: MessageSquare },
  { to: "/documents", label: "Documents", icon: FileText },
  { to: "/voice", label: "Voice", icon: Mic },
  { to: "/history", label: "History", icon: History },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
] as const

export function AppShell({ children }: { children: ReactNode }) {
  const { theme, toggleTheme } = useTheme()
  const { settings, setUserName } = useSettings()
  const pathname = useRouterState({ select: (s) => s.location.pathname })

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="flex w-64 shrink-0 flex-col border-r border-border p-4">
        <div className="mb-6 flex items-center gap-2 px-2">
          <div
            className="flex h-9 w-9 items-center justify-center rounded-xl"
            style={{ background: "var(--gradient-primary)" }}
          >
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-semibold leading-none">CARA</p>
            <p className="text-xs text-muted-foreground">Research Agent</p>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => {
            const active = pathname === to
            return (
              <Link
                key={to}
                to={to}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground/80 hover:bg-secondary/60"
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            )
          })}
        </nav>

        <div className="flex flex-col gap-2 border-t border-border pt-3">
          <button
            onClick={toggleTheme}
            className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-foreground/80 hover:bg-secondary/60"
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
            {theme === "dark" ? "Light mode" : "Dark mode"}
          </button>

          <div className="flex items-center justify-between rounded-xl px-3 py-2 text-xs text-muted-foreground">
            <span className="truncate">Signed in as {settings.userName}</span>
            <button
              onClick={() => setUserName("")}
              title="Sign out"
              className="ml-2 shrink-0 hover:text-foreground"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-hidden">{children}</main>
    </div>
  )
}
