import { useCallback, useRef, useState } from "react"
import { createFileRoute } from "@tanstack/react-router"
import { motion } from "framer-motion"
import { Mic, Square, AlertCircle, Volume2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { sendVoice, ApiError } from "@/lib/api"
import type { ChatMessage, VoiceResponse } from "@/types"
import { cn } from "@/lib/utils"
import { useConversations } from "@/hooks/useConversations"

export const Route = createFileRoute("/_app/voice")({
  component: VoicePage,
})

type VoiceState = "idle" | "listening" | "processing" | "finished" | "error"

const MIN_RECORDING_MS = 2000 // enforce a minimum clip length so Whisper has enough signal

function makeMessage(role: ChatMessage["role"], content: string): ChatMessage {
  return { id: crypto.randomUUID(), role, content, createdAt: Date.now() }
}

function VoicePage() {
  const [state, setState] = useState<VoiceState>("idle")
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [result, setResult] = useState<VoiceResponse | null>(null)
  const { activeId, createConversation, appendMessage } = useConversations()

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const recordingStartRef = useRef<number>(0)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const stopStream = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
  }

  const startRecording = useCallback(async () => {
    setErrorMessage(null)
    setResult(null)

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" })
      mediaRecorderRef.current = recorder
      chunksRef.current = []
      recordingStartRef.current = Date.now()

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        stopStream()
        const elapsed = Date.now() - recordingStartRef.current

        if (elapsed < MIN_RECORDING_MS) {
          setState("error")
          setErrorMessage(
            `Recording was too short (${(elapsed / 1000).toFixed(1)}s). ` +
              "Please record at least 2-3 seconds so speech can be recognized clearly."
          )
          return
        }

        const blob = new Blob(chunksRef.current, { type: "audio/webm" })
        setState("processing")

        try {
          const response = await sendVoice(blob)
          setResult(response)
          setState("finished")

          // Record this exchange in the same history used by text chat, so
          // voice conversations show up on the History page too.
          let conversationId = activeId
          if (!conversationId) {
            conversationId = createConversation()
          }
          appendMessage(conversationId, makeMessage("user", `🎤 ${response.user_said}`))
          appendMessage(conversationId, makeMessage("assistant", response.answer))

          // Autoplay the returned answer.
          const audioUrl = `data:audio/mp3;base64,${response.audio_base64}`
          if (audioRef.current) {
            audioRef.current.src = audioUrl
            audioRef.current.play().catch(() => {
              // Autoplay can be blocked by the browser; the visible <audio>
              // controls still let the user press play manually.
            })
          }
        } catch (err) {
          const message =
            err instanceof ApiError ? err.message : "Voice processing failed unexpectedly."
          setErrorMessage(message)
          setState("error")
        }
      }

      recorder.start()
      setState("listening")
    } catch (err) {
      stopStream()
      setState("error")
      if (err instanceof DOMException && (err.name === "NotAllowedError" || err.name === "PermissionDeniedError")) {
        setErrorMessage(
          "Microphone access was denied. Please allow microphone permissions " +
            "in your browser's site settings and try again."
        )
      } else {
        setErrorMessage("Could not access the microphone on this device.")
      }
    }
  }, [activeId, createConversation, appendMessage])

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop()
  }, [])

  const reset = () => {
    setState("idle")
    setErrorMessage(null)
    setResult(null)
  }

  return (
    <div className="flex h-screen flex-col items-center justify-center gap-8 p-6">
      <div className="text-center">
        <h1 className="text-xl font-semibold">Voice Assistant</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Speak in English, Telugu, Hindi, Tamil, Malayalam, or Kannada.
        </p>
      </div>

      <div className="relative flex h-40 w-40 items-center justify-center">
        {state === "listening" && (
          <>
            <span
              className="absolute inset-0 rounded-full animate-pulse-ring"
              style={{ background: "var(--gradient-primary)" }}
            />
            <span
              className="absolute inset-0 rounded-full animate-pulse-ring [animation-delay:0.5s]"
              style={{ background: "var(--gradient-primary)" }}
            />
          </>
        )}

        <button
          onClick={state === "listening" ? stopRecording : startRecording}
          disabled={state === "processing"}
          className={cn(
            "relative flex h-28 w-28 items-center justify-center rounded-full text-white shadow-lg transition-transform active:scale-95 disabled:opacity-70"
          )}
          style={{ background: "var(--gradient-primary)" }}
        >
          {state === "listening" ? (
            <Square className="h-8 w-8" />
          ) : (
            <Mic className="h-10 w-10" />
          )}
        </button>
      </div>

      <div className="min-h-[1.5rem] text-sm font-medium text-muted-foreground">
        {state === "idle" && "Tap the mic to start"}
        {state === "listening" && "Listening... tap again to stop"}
        {state === "processing" && "Processing your question..."}
        {state === "finished" && "Done — here's what CARA heard and said"}
        {state === "error" && "Something went wrong"}
      </div>

      {errorMessage && (
        <div className="flex max-w-md items-center gap-2 rounded-xl bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {errorMessage}
        </div>
      )}

      {result && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass w-full max-w-md rounded-2xl p-5"
        >
          <div className="mb-3">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">
              You said ({result.detected_language})
            </p>
            <p className="text-sm">{result.user_said}</p>
          </div>
          <div className="mb-3">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">
              CARA's answer
            </p>
            <p className="text-sm">{result.answer}</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Volume2 className="h-3.5 w-3.5" />
            Playing response audio
          </div>
        </motion.div>
      )}

      {/* Hidden until playback starts; controls shown once we have audio so
          the user can replay it if autoplay was blocked. */}
      <audio ref={audioRef} controls className={cn(result ? "block" : "hidden")} />

      {(state === "finished" || state === "error") && (
        <Button variant="outline" onClick={reset}>
          Ask another question
        </Button>
      )}
    </div>
  )
}
