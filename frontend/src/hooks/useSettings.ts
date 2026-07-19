import { useCallback, useEffect, useState } from "react"

const STORAGE_KEY = "cara.settings.v1"

export interface Settings {
  userName: string
  voiceLanguageHint: string // informational only; Whisper auto-detects
  hasSignedInBefore: boolean
}

const DEFAULT_SETTINGS: Settings = {
  userName: "",
  voiceLanguageHint: "auto",
  hasSignedInBefore: false,
}

function load(): Settings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return DEFAULT_SETTINGS
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
  } catch {
    return DEFAULT_SETTINGS
  }
}

/**
 * Simple mock auth + preferences, stored in localStorage only. There's no
 * real authentication backend in this build — see README for how this
 * simplification was made and how to replace it with real auth later.
 */
export function useSettings() {
  const [settings, setSettings] = useState<Settings>(load)
  const [justSignedIn, setJustSignedIn] = useState(false)

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  }, [settings])

  const setUserName = useCallback((userName: string) => {
    setSettings((prev) => {
      // If a name is being set for the first time (i.e. signing in, not
      // signing out), flag it so the UI can show a one-time greeting, and
      // remember that this browser has signed in before for next time.
      const isSigningIn = userName.trim().length > 0 && prev.userName.trim().length === 0
      if (isSigningIn) setJustSignedIn(true)
      return {
        ...prev,
        userName,
        hasSignedInBefore: isSigningIn ? true : prev.hasSignedInBefore,
      }
    })
  }, [])

  const setVoiceLanguageHint = useCallback((voiceLanguageHint: string) => {
    setSettings((prev) => ({ ...prev, voiceLanguageHint }))
  }, [])

  const acknowledgeGreeting = useCallback(() => {
    setJustSignedIn(false)
  }, [])

  const isLoggedIn = settings.userName.trim().length > 0

  return {
    settings,
    isLoggedIn,
    justSignedIn,
    acknowledgeGreeting,
    setUserName,
    setVoiceLanguageHint,
  }
}
