import { useEffect, useRef, useState } from "react"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { motion, AnimatePresence } from "framer-motion"
import { Send, Mic, Paperclip, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { useConversations } from "@/hooks/useConversations"
import { useSettings } from "@/hooks/useSettings"
import { chat, ApiError } from "@/lib/api"
import type { ChatMessage } from "@/types"
import { cn } from "@/lib/utils"

export const Route = createFileRoute("/_app/chat")({
  component: ChatPage,
})

function makeMessage(role: ChatMessage["role"], content: string): ChatMessage {
  return { id: crypto.randomUUID(), role, content, createdAt: Date.now() }
}

function ChatPage() {
  const navigate = useNavigate()
  const { conversations, activeId, createConversation, appendMessage } =
    useConversations()
  const { settings, justSignedIn, acknowledgeGreeting } = useSettings()

  const [input, setInput] = useState("")
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  const activeConversation = conversations.find((c) => c.id === activeId)
  const messages = activeConversation?.messages ?? []

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
  }, [messages.length, isSending])

  useEffect(() => {
    if (!justSignedIn) return
    const timer = setTimeout(acknowledgeGreeting, 4000)
    return () => clearTimeout(timer)
  }, [justSignedIn, acknowledgeGreeting])

  const handleSend = async () => {
    const question = input.trim()
    if (!question || isSending) return

    setError(null)
    setInput("")

    let conversationId = activeId
    if (!conversationId) {
      conversationId = createConversation()
    }

    appendMessage(conversationId, makeMessage("user", question))
    setIsSending(true)

    try {
      const response = await chat(question)
      appendMessage(conversationId, makeMessage("assistant", response.answer))
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Something went wrong reaching CARA."
      setError(message)
      appendMessage(
        conversationId,
        makeMessage("assistant", `⚠️ ${message}`)
      )
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-screen flex-col">
      <header className="border-b border-border px-6 py-4">
        <h1 className="text-lg font-semibold">
          {activeConversation?.title ?? "New conversation"}
        </h1>
        <p className="text-xs text-muted-foreground">
          CARA decides on its own whether to answer directly, search your
          documents, search the web, or calculate.
        </p>
      </header>

      <AnimatePresence>
        {justSignedIn && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden px-6"
          >
            <div
              className="my-3 rounded-xl px-4 py-3 text-sm font-medium text-white"
              style={{ background: "var(--gradient-primary)" }}
            >
              {settings.hasSignedInBefore
                ? `Welcome back, ${settings.userName}! 👋`
                : `Welcome, ${settings.userName}! Great to meet you.`}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-muted-foreground">
            <p className="text-base font-medium">
              {settings.userName ? `Hi ${settings.userName}, ask CARA anything` : "Ask CARA anything"}
            </p>
            <p className="text-sm">
              Try a general question, something about an uploaded PDF, or a
              calculation.
            </p>
          </div>
        )}

        <div className="mx-auto flex max-w-3xl flex-col gap-4">
          <AnimatePresence initial={false}>
            {messages.map((m) => (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                className={cn(
                  "flex",
                  m.role === "user" ? "justify-end" : "justify-start"
                )}
              >
                <div
                  className={cn(
                    "max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
                    m.role === "user"
                      ? "text-primary-foreground"
                      : "glass"
                  )}
                  style={
                    m.role === "user"
                      ? { background: "var(--gradient-primary)" }
                      : undefined
                  }
                >
                  {m.content}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {isSending && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="glass flex items-center gap-1 rounded-2xl px-4 py-3">
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground" />
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {error && (
        <div className="mx-6 mb-2 flex items-center gap-2 rounded-xl bg-destructive/10 px-4 py-2 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      <div className="border-t border-border p-4">
        <div className="mx-auto flex max-w-3xl items-end gap-2">
          <Button
            type="button"
            variant="outline"
            size="icon"
            title="Upload a document"
            onClick={() => navigate({ to: "/documents" })}
          >
            <Paperclip className="h-4 w-4" />
          </Button>

          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message CARA... (Enter to send, Shift+Enter for a new line)"
            rows={1}
            className="max-h-40 min-h-[44px] flex-1"
          />

          <Button
            type="button"
            variant="outline"
            size="icon"
            title="Switch to voice mode"
            onClick={() => navigate({ to: "/voice" })}
          >
            <Mic className="h-4 w-4" />
          </Button>

          <Button
            type="button"
            size="icon"
            title="Send"
            disabled={!input.trim() || isSending}
            onClick={handleSend}
            style={{ background: "var(--gradient-primary)" }}
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
