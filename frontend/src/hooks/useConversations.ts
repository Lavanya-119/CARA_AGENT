import { useCallback, useEffect, useState } from "react"
import type { ChatMessage, Conversation } from "@/types"

const STORAGE_KEY = "cara.conversations.v1"

function loadConversations(): Conversation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    return JSON.parse(raw) as Conversation[]
  } catch {
    return []
  }
}

function persist(conversations: Conversation[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
  } catch {
    // localStorage can throw in private browsing / quota-exceeded cases.
    // Silently skip persistence rather than crash the chat experience.
  }
}

function titleFromMessage(text: string): string {
  const trimmed = text.trim()
  if (trimmed.length <= 48) return trimmed || "New conversation"
  return trimmed.slice(0, 48).trimEnd() + "…"
}

/**
 * Manages chat history in localStorage. There is no backend persistence
 * endpoint in this build, so history lives client-side per browser. See the
 * README for how to add a `/history` endpoint backed by a real database if
 * cross-device history is needed later.
 */
export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>(() =>
    loadConversations()
  )
  const [activeId, setActiveId] = useState<string | null>(
    () => conversations[0]?.id ?? null
  )

  useEffect(() => {
    persist(conversations)
  }, [conversations])

  const createConversation = useCallback((): string => {
    const id = crypto.randomUUID()
    const newConversation: Conversation = {
      id,
      title: "New conversation",
      messages: [],
      updatedAt: Date.now(),
    }
    setConversations((prev) => [newConversation, ...prev])
    setActiveId(id)
    return id
  }, [])

  const appendMessage = useCallback(
    (conversationId: string, message: ChatMessage) => {
      setConversations((prev) => {
        const exists = prev.some((c) => c.id === conversationId)
        if (!exists) {
          const fresh: Conversation = {
            id: conversationId,
            title:
              message.role === "user"
                ? titleFromMessage(message.content)
                : "New conversation",
            messages: [message],
            updatedAt: Date.now(),
          }
          return [fresh, ...prev]
        }
        return prev.map((c) => {
          if (c.id !== conversationId) return c
          const messages = [...c.messages, message]
          const title =
            c.messages.length === 0 && message.role === "user"
              ? titleFromMessage(message.content)
              : c.title
          return { ...c, messages, title, updatedAt: Date.now() }
        })
      })
    },
    []
  )

  const deleteConversation = useCallback(
    (conversationId: string) => {
      setConversations((prev) => prev.filter((c) => c.id !== conversationId))
      setActiveId((prev) => (prev === conversationId ? null : prev))
    },
    []
  )

  const clearAll = useCallback(() => {
    setConversations([])
    setActiveId(null)
  }, [])

  const sorted = [...conversations].sort((a, b) => b.updatedAt - a.updatedAt)

  return {
    conversations: sorted,
    activeId,
    setActiveId,
    createConversation,
    appendMessage,
    deleteConversation,
    clearAll,
  }
}
