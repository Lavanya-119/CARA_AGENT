import { useCallback, useEffect, useState } from "react"
import type { IndexedDocument } from "@/types"

const STORAGE_KEY = "cara.documents.v1"

function load(): IndexedDocument[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    return JSON.parse(raw) as IndexedDocument[]
  } catch {
    return []
  }
}

/**
 * Tracks which PDFs the user has uploaded, client-side. The backend indexes
 * chunks into a persistent Chroma store but doesn't expose a "list uploaded
 * files" endpoint in this build, so this list is a local record of what this
 * browser has sent — it won't reflect uploads made from another device.
 */
export function useDocuments() {
  const [documents, setDocuments] = useState<IndexedDocument[]>(load)

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(documents))
  }, [documents])

  const addDocument = useCallback((doc: IndexedDocument) => {
    setDocuments((prev) => [doc, ...prev])
  }, [])

  const removeDocument = useCallback((id: string) => {
    setDocuments((prev) => prev.filter((d) => d.id !== id))
  }, [])

  return { documents, addDocument, removeDocument }
}
