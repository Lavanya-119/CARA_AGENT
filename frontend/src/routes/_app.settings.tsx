import { createFileRoute } from "@tanstack/react-router"
import { Sun, Moon } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useTheme } from "@/hooks/useTheme"
import { useSettings } from "@/hooks/useSettings"
import { cn } from "@/lib/utils"

export const Route = createFileRoute("/_app/settings")({
  component: SettingsPage,
})

const LANGUAGE_OPTIONS = [
  { value: "auto", label: "Auto-detect (recommended)" },
  { value: "en", label: "English" },
  { value: "hi", label: "Hindi" },
  { value: "te", label: "Telugu" },
  { value: "ta", label: "Tamil" },
  { value: "ml", label: "Malayalam" },
  { value: "kn", label: "Kannada" },
]

function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const { settings, setVoiceLanguageHint } = useSettings()

  return (
    <div className="mx-auto flex h-screen max-w-2xl flex-col gap-6 overflow-y-auto p-8">
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Preferences are stored locally in this browser.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Choose how CARA looks.</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-3">
          <button
            onClick={() => setTheme("light")}
            className={cn(
              "flex flex-1 flex-col items-center gap-2 rounded-xl border p-4 text-sm font-medium",
              theme === "light" ? "border-primary bg-primary/5" : "border-border"
            )}
          >
            <Sun className="h-5 w-5" />
            Light
          </button>
          <button
            onClick={() => setTheme("dark")}
            className={cn(
              "flex flex-1 flex-col items-center gap-2 rounded-xl border p-4 text-sm font-medium",
              theme === "dark" ? "border-primary bg-primary/5" : "border-border"
            )}
          >
            <Moon className="h-5 w-5" />
            Dark
          </button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Voice language</CardTitle>
          <CardDescription>
            CARA auto-detects the spoken language automatically. This is just
            a display hint for your own reference.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <select
            value={settings.voiceLanguageHint}
            onChange={(e) => setVoiceLanguageHint(e.target.value)}
            className="h-11 w-full rounded-xl border border-input bg-card px-4 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {LANGUAGE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
          <CardDescription>
            CARA currently uses a simple local session rather than real
            authentication.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm">
            Signed in as <span className="font-medium">{settings.userName}</span>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
