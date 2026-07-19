import { useState } from "react"
import { motion } from "framer-motion"
import { Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export function LoginGate({ onLogin }: { onLogin: (name: string) => void }) {
  const [name, setName] = useState("")

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = name.trim()
    if (trimmed) onLogin(trimmed)
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card className="glass w-[360px]">
          <CardHeader className="items-center text-center">
            <div
              className="mb-2 flex h-12 w-12 items-center justify-center rounded-2xl"
              style={{ background: "var(--gradient-primary)" }}
            >
              <Sparkles className="h-6 w-6 text-white" />
            </div>
            <CardTitle>Welcome to CARA</CardTitle>
            <CardDescription>
              Conversational AI Research Agent — sign in to start chatting.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={submit} className="flex flex-col gap-3">
              <input
                autoFocus
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your name"
                className="h-11 rounded-xl border border-input bg-card px-4 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
              <Button type="submit" size="lg" disabled={!name.trim()}>
                Continue
              </Button>
              <p className="text-center text-xs text-muted-foreground">
                This is a simple local session — no password, no server-side
                account. Your name is stored only in this browser.
              </p>
            </form>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
