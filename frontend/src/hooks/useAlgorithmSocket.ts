import { useCallback, useEffect, useRef, useState } from "react"
import type { AlgorithmStep } from "@/types"

export interface SocketEvent {
  type: "RUN_STARTED" | "ALGORITHM_STEP" | "ALGORITHM_COMPLETE"
  [key: string]: unknown
}

/**
 * Connects to the backend's live algorithm-progress WebSocket channel
 * (`/api/v1/ws/algorithm/{channel}`) and accumulates the real steps the
 * algorithm emitted as it ran (see app/algorithms/result.py on the backend -
 * nothing here is client-side fabricated, it is a replay of the actual trace).
 */
export function useAlgorithmSocket(channel: string | null) {
  const [connected, setConnected] = useState(false)
  const [steps, setSteps] = useState<AlgorithmStep[]>([])
  const [complete, setComplete] = useState(false)
  const [running, setRunning] = useState(false)
  const socketRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!channel) return

    const proto = window.location.protocol === "https:" ? "wss" : "ws"
    const socket = new WebSocket(`${proto}://${window.location.host}/api/v1/ws/algorithm/${channel}`)
    socketRef.current = socket

    socket.onopen = () => setConnected(true)
    socket.onclose = () => setConnected(false)
    socket.onmessage = (event) => {
      const msg: SocketEvent = JSON.parse(event.data)
      if (msg.type === "RUN_STARTED") {
        setSteps([])
        setComplete(false)
        setRunning(true)
      } else if (msg.type === "ALGORITHM_STEP") {
        setSteps((prev) => [...prev, msg as unknown as AlgorithmStep])
      } else if (msg.type === "ALGORITHM_COMPLETE") {
        setComplete(true)
        setRunning(false)
      }
    }

    return () => {
      socket.close()
      socketRef.current = null
    }
  }, [channel])

  const reset = useCallback(() => {
    setSteps([])
    setComplete(false)
    setRunning(false)
  }, [])

  return { connected, steps, complete, running, reset }
}
