import type { ChatResponse, UploadResponse, VoiceResponse } from "@/types"

const API_URL = import.meta.env.VITE_API_URL as string | undefined

/**
 * A small, explicit error type so UI code can show something meaningful
 * instead of a generic "something went wrong".
 */
export class ApiError extends Error {
  constructor(message: string) {
    super(message)
    this.name = "ApiError"
  }
}

function requireApiUrl(): string {
  if (!API_URL) {
    throw new ApiError(
      "VITE_API_URL is not set. Create a .env file in the frontend project root " +
        "with VITE_API_URL=http://localhost:8000 and restart the dev server."
    )
  }
  return API_URL
}

async function parseErrorResponse(response: Response): Promise<string> {
  try {
    const data = await response.json()
    if (typeof data?.detail === "string") return data.detail
    return JSON.stringify(data)
  } catch {
    return `${response.status} ${response.statusText}`
  }
}

export async function health(): Promise<boolean> {
  try {
    const base = requireApiUrl()
    const res = await fetch(`${base}/health`)
    if (!res.ok) return false
    const data = await res.json()
    return data?.status === "ok"
  } catch {
    return false
  }
}

export async function chat(question: string): Promise<ChatResponse> {
  const base = requireApiUrl()
  try {
    const res = await fetch(`${base}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    })
    if (!res.ok) {
      throw new ApiError(await parseErrorResponse(res))
    }
    return (await res.json()) as ChatResponse
  } catch (err) {
    if (err instanceof ApiError) throw err
    throw new ApiError(
      "Could not reach CARA's backend. Is it running and is VITE_API_URL correct?"
    )
  }
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const base = requireApiUrl()
  const formData = new FormData()
  formData.append("file", file)

  try {
    const res = await fetch(`${base}/upload-document`, {
      method: "POST",
      body: formData,
    })
    if (!res.ok) {
      throw new ApiError(await parseErrorResponse(res))
    }
    return (await res.json()) as UploadResponse
  } catch (err) {
    if (err instanceof ApiError) throw err
    throw new ApiError(
      "Upload failed. Check that CARA's backend is running and reachable."
    )
  }
}

export async function sendVoice(blob: Blob): Promise<VoiceResponse> {
  const base = requireApiUrl()
  const formData = new FormData()
  formData.append("file", blob, "recording.webm")

  try {
    const res = await fetch(`${base}/voice`, {
      method: "POST",
      body: formData,
    })
    if (!res.ok) {
      throw new ApiError(await parseErrorResponse(res))
    }
    return (await res.json()) as VoiceResponse
  } catch (err) {
    if (err instanceof ApiError) throw err
    throw new ApiError(
      "Voice request failed. Check that CARA's backend is running and reachable."
    )
  }
}
