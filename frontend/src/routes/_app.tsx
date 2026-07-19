import { createFileRoute, Outlet } from "@tanstack/react-router"
import { useSettings } from "@/hooks/useSettings"
import { LoginGate } from "@/components/LoginGate"
import { AppShell } from "@/components/AppShell"

export const Route = createFileRoute("/_app")({
  component: AppLayout,
})

function AppLayout() {
  const { isLoggedIn, setUserName } = useSettings()

  if (!isLoggedIn) {
    return <LoginGate onLogin={setUserName} />
  }

  return (
    <AppShell>
      <Outlet />
    </AppShell>
  )
}
