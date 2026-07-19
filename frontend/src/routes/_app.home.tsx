import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { motion } from "framer-motion"
import {
  MessageSquare,
  FileText,
  Mic,
  Globe,
  ChevronRight,
} from "lucide-react"
import { useSettings } from "@/hooks/useSettings"
import { useConversations } from "@/hooks/useConversations"

export const Route = createFileRoute("/_app/home")({
  component: HomePage,
})

function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return "Good Morning"
  if (hour < 17) return "Good Afternoon"
  return "Good Evening"
}

const FEATURE_CARDS = [
  {
    to: "/chat" as const,
    icon: MessageSquare,
    title: "Start Chat",
    description: "Ask anything, brainstorm, or draft.",
  },
  {
    to: "/documents" as const,
    icon: FileText,
    title: "Ask Documents",
    description: "Upload and query your files.",
  },
  {
    to: "/voice" as const,
    icon: Mic,
    title: "Voice Assistant",
    description: "Talk to CARA hands-free.",
  },
  {
    to: "/chat" as const,
    icon: Globe,
    title: "Research",
    description: "Deep-dive the web with sources.",
  },
]

function HomePage() {
  const navigate = useNavigate()
  const { settings } = useSettings()
  const { conversations, setActiveId } = useConversations()

  const recentChats = conversations.slice(0, 4)

  const openConversation = (id: string) => {
    setActiveId(id)
    navigate({ to: "/chat" })
  }

  return (
    <div className="h-screen overflow-y-auto p-8">
      <div className="mx-auto max-w-5xl">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <p className="text-muted-foreground">{getGreeting()},</p>
          <h1
            className="mt-1 bg-clip-text text-4xl font-bold text-transparent"
            style={{ backgroundImage: "var(--gradient-primary)" }}
          >
            {settings.userName}
          </h1>
          <p className="mt-3 text-lg text-muted-foreground">
            How can CARA help today?
          </p>
        </motion.div>

        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURE_CARDS.map(({ to, icon: Icon, title, description }, i) => (
            <motion.button
              key={title}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: i * 0.05 }}
              onClick={() => navigate({ to })}
              className="glass group flex flex-col items-start gap-4 rounded-2xl p-5 text-left transition-transform hover:-translate-y-0.5"
            >
              <div className="flex w-full items-center justify-between">
                <div
                  className="flex h-10 w-10 items-center justify-center rounded-xl"
                  style={{ background: "var(--gradient-primary)" }}
                >
                  <Icon className="h-5 w-5 text-white" />
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
              </div>
              <div>
                <p className="font-semibold">{title}</p>
                <p className="mt-0.5 text-sm text-muted-foreground">
                  {description}
                </p>
              </div>
            </motion.button>
          ))}
        </div>

        <div className="mt-10">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Recent chats</h2>
            <button
              onClick={() => navigate({ to: "/history" })}
              className="text-sm font-medium text-primary hover:underline"
            >
              View all
            </button>
          </div>

          {recentChats.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No conversations yet — tap Start Chat to begin one.
            </p>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {recentChats.map((c) => (
                <button
                  key={c.id}
                  onClick={() => openConversation(c.id)}
                  className="glass rounded-2xl px-5 py-4 text-left text-sm font-medium hover:bg-secondary/40"
                >
                  {c.title}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
