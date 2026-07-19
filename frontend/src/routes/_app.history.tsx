import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { motion, AnimatePresence } from "framer-motion"
import { MessageSquare, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useConversations } from "@/hooks/useConversations"

export const Route = createFileRoute("/_app/history")({
  component: HistoryPage,
})

function HistoryPage() {
  const navigate = useNavigate()
  const { conversations, setActiveId, deleteConversation, clearAll } = useConversations()

  const openConversation = (id: string) => {
    setActiveId(id)
    navigate({ to: "/chat" })
  }

  return (
    <div className="mx-auto flex h-screen max-w-3xl flex-col gap-6 overflow-y-auto p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Chat History</h1>
          <p className="text-sm text-muted-foreground">
            Stored locally in this browser — pick a conversation to continue it.
          </p>
        </div>
        {conversations.length > 0 && (
          <Button variant="outline" size="sm" onClick={clearAll}>
            Clear all
          </Button>
        )}
      </div>

      {conversations.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No conversations yet. Start chatting to build up history.
        </p>
      )}

      <div className="flex flex-col gap-2">
        <AnimatePresence initial={false}>
          {conversations.map((c) => (
            <motion.div
              key={c.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, height: 0 }}
              className="glass flex items-center justify-between rounded-xl px-4 py-3"
            >
              <button
                onClick={() => openConversation(c.id)}
                className="flex flex-1 items-center gap-3 text-left"
              >
                <MessageSquare className="h-5 w-5 shrink-0 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">{c.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {c.messages.length} messages ·{" "}
                    {new Date(c.updatedAt).toLocaleString()}
                  </p>
                </div>
              </button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => deleteConversation(c.id)}
                title="Delete conversation"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
