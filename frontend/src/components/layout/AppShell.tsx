import { Outlet, useLocation } from "react-router-dom"
import { AnimatePresence, motion } from "framer-motion"
import { Sidebar } from "@/components/layout/Sidebar"
import { Topbar } from "@/components/layout/Topbar"
import { CommandPalette } from "@/components/common/CommandPalette"

const TITLES: Record<string, string> = {
  "/app/dashboard": "Dashboard",
  "/app/students": "Student Management",
  "/app/labs": "Laboratory Management",
  "/app/config": "Allocation Configuration",
  "/app/graph": "Graph Visualization",
  "/app/playground": "Algorithm Playground",
  "/app/results": "Allocation Results",
  "/app/analytics": "Analytics",
  "/app/insights": "Allocation Insights",
  "/app/atlas": "Algorithm Atlas",
  "/app/concepts": "Concept Lab",
  "/app/ai": "AI Command Center",
  "/app/simulator": "What-If Simulator",
}

export function AppShell() {
  const location = useLocation()
  const title = TITLES[location.pathname] ?? "AllocateX"

  return (
    <div className="flex h-screen bg-canvas bg-grid">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar title={title} />
        <main className="flex-1 overflow-y-auto p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
      <CommandPalette />
    </div>
  )
}
