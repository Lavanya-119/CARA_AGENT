export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  createdAt: number
}

export interface Conversation {
  id: string
  title: string
  messages: ChatMessage[]
  updatedAt: number
}

export interface ChatResponse {
  answer: string
}

export interface UploadResponse {
  status: string
  chunks_indexed: number
}

export interface VoiceResponse {
  user_said: string
  detected_language: string
  english_question: string
  answer: string
  audio_base64: string
}

export interface IndexedDocument {
  id: string
  name: string
  chunksIndexed: number
  uploadedAt: number
  status: "success" | "error"
  errorMessage?: string
}
