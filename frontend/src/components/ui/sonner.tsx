import { Toaster as SonnerToaster } from "sonner"

export function Toaster() {
  return (
    <SonnerToaster
      theme="dark"
      position="top-right"
      toastOptions={{
        style: {
          background: "rgba(18,18,22,0.95)",
          border: "1px solid rgba(255,255,255,0.12)",
          color: "#fff",
          backdropFilter: "blur(12px)",
        },
      }}
    />
  )
}
