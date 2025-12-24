import { useEffect, useRef } from 'react'

type UsePollingOptions<T> = {
  enabled: boolean
  pollFn: () => Promise<T>
  intervalMs?: number
  onResult: (value: T) => void
  onError?: (err: unknown) => void
  stopWhen?: (value: T) => boolean
}

export function usePolling<T>({
  enabled,
  pollFn,
  intervalMs = 2500,
  onResult,
  onError,
  stopWhen,
}: UsePollingOptions<T>) {
  const timerRef = useRef<number | null>(null)

  useEffect(() => {
    if (!enabled) return
    let cancelled = false

    const poll = async () => {
      try {
        const value = await pollFn()
        onResult(value)
        if (stopWhen && stopWhen(value)) return
      } catch (err) {
        onError?.(err)
      }
      if (!cancelled) {
        timerRef.current = window.setTimeout(poll, intervalMs)
      }
    }

    poll()

    return () => {
      cancelled = true
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
    }
  }, [enabled, pollFn, intervalMs, onResult, onError, stopWhen])
}

