import { lazy, Suspense } from "react"
import { Navigate, Route, Routes } from "react-router-dom"
import { ProtectedRoute } from "@/components/layout/ProtectedRoute"
import { AppShell } from "@/components/layout/AppShell"
import { ErrorBoundary } from "@/components/common/ErrorBoundary"
import { Skeleton } from "@/components/ui/skeleton"

// each page is its own chunk, so a route only downloads the code (and charting/graph libraries) it uses
const LandingPage = lazy(() => import("@/pages/LandingPage"))
const LoginPage = lazy(() => import("@/pages/LoginPage"))
const RegisterPage = lazy(() => import("@/pages/RegisterPage"))
const DashboardPage = lazy(() => import("@/pages/DashboardPage"))
const StudentsPage = lazy(() => import("@/pages/StudentsPage"))
const LabsPage = lazy(() => import("@/pages/LabsPage"))
const AllocationConfigPage = lazy(() => import("@/pages/AllocationConfigPage"))
const GraphVisualizationPage = lazy(() => import("@/pages/GraphVisualizationPage"))
const AlgorithmPlaygroundPage = lazy(() => import("@/pages/AlgorithmPlaygroundPage"))
const AllocationResultsPage = lazy(() => import("@/pages/AllocationResultsPage"))
const AnalyticsPage = lazy(() => import("@/pages/AnalyticsPage"))
const AICommandCenterPage = lazy(() => import("@/pages/AICommandCenterPage"))
const WhatIfSimulatorPage = lazy(() => import("@/pages/WhatIfSimulatorPage"))
const AlgorithmAtlasPage = lazy(() => import("@/pages/AlgorithmAtlasPage"))
const ConceptLabPage = lazy(() => import("@/pages/ConceptLabPage"))
const InsightsPage = lazy(() => import("@/pages/InsightsPage"))

function wrap(node: React.ReactNode) {
  return (
    <ErrorBoundary>
      <Suspense fallback={<Skeleton className="h-96 w-full" />}>{node}</Suspense>
    </ErrorBoundary>
  )
}

function PublicPage({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<div className="min-h-screen bg-canvas" />}>{children}</Suspense>
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<PublicPage><LandingPage /></PublicPage>} />
      <Route path="/login" element={<PublicPage><LoginPage /></PublicPage>} />
      <Route path="/register" element={<PublicPage><RegisterPage /></PublicPage>} />

      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={wrap(<DashboardPage />)} />
        <Route
          path="students"
          element={
            <ProtectedRoute roles={["ADMIN", "FACULTY"]}>{wrap(<StudentsPage />)}</ProtectedRoute>
          }
        />
        <Route
          path="labs"
          element={<ProtectedRoute roles={["ADMIN", "FACULTY"]}>{wrap(<LabsPage />)}</ProtectedRoute>}
        />
        <Route
          path="config"
          element={
            <ProtectedRoute roles={["ADMIN", "FACULTY"]}>{wrap(<AllocationConfigPage />)}</ProtectedRoute>
          }
        />
        <Route path="graph" element={wrap(<GraphVisualizationPage />)} />
        <Route path="playground" element={wrap(<AlgorithmPlaygroundPage />)} />
        <Route path="results" element={wrap(<AllocationResultsPage />)} />
        <Route path="analytics" element={wrap(<AnalyticsPage />)} />
        <Route path="insights" element={wrap(<InsightsPage />)} />
        <Route path="atlas" element={wrap(<AlgorithmAtlasPage />)} />
        <Route path="concepts" element={wrap(<ConceptLabPage />)} />
        <Route
          path="ai"
          element={<ProtectedRoute roles={["ADMIN", "FACULTY"]}>{wrap(<AICommandCenterPage />)}</ProtectedRoute>}
        />
        <Route
          path="simulator"
          element={
            <ProtectedRoute roles={["ADMIN", "FACULTY"]}>{wrap(<WhatIfSimulatorPage />)}</ProtectedRoute>
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
