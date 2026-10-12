import { useState } from "react"
import { toast } from "sonner"
import { Sparkles, Send, AlertTriangle, FileText, MessageSquareQuote } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { useAICommand, useAIAnalyticsQuery, useAIConflicts, useAIReport } from "@/hooks/useAI"
import { apiErrorMessage } from "@/lib/api"

const EXAMPLE_COMMANDS = [
  "Allocate second year CSE students to AI and DBMS labs while prioritizing their first preference.",
  "Only allocate IT students to their own department labs.",
  "Run a fair allocation for third year students with a department cap.",
]

const EXAMPLE_QUESTIONS = [
  "Why are students unmatched?",
  "What is the current lab utilization?",
  "Which algorithm performed fastest?",
]

export default function AICommandCenterPage() {
  const [text, setText] = useState("")
  const [autoExecute, setAutoExecute] = useState(false)
  const [question, setQuestion] = useState("")

  const command = useAICommand()
  const analyticsQuery = useAIAnalyticsQuery()
  const { data: conflicts, isLoading: conflictsLoading } = useAIConflicts()
  const report = useAIReport()

  async function onSendCommand() {
    if (!text.trim()) return
    try {
      await command.mutateAsync({ text, auto_execute: autoExecute })
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  async function onAskQuestion() {
    if (!question.trim()) return
    try {
      await analyticsQuery.mutateAsync({ question })
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className="flex items-center gap-2">
        <div className="rounded-lg bg-gradient-to-br from-brand-500 to-violet-500 p-2">
          <Sparkles className="h-4 w-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-medium text-ink">AI Command Center</p>
          <p className="text-xs text-ink-muted">Natural language is parsed into structured constraints — the deterministic engine still decides every match.</p>
        </div>
      </div>

      <Tabs defaultValue="command">
        <TabsList>
          <TabsTrigger value="command">Allocation Command</TabsTrigger>
          <TabsTrigger value="ask">Ask Analytics</TabsTrigger>
          <TabsTrigger value="conflicts">Conflicts</TabsTrigger>
          <TabsTrigger value="report">Report</TabsTrigger>
        </TabsList>

        <TabsContent value="command">
          <Card>
            <CardHeader>
              <CardTitle>Describe the allocation you want</CardTitle>
              <CardDescription>The AI extracts department/year/lab filters and constraint weights — it never invents results itself.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Textarea
                placeholder="e.g. Allocate second year CSE students to AI and DBMS labs while prioritizing their first preference."
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={3}
              />
              <div className="flex flex-wrap gap-1.5">
                {EXAMPLE_COMMANDS.map((c) => (
                  <button key={c} onClick={() => setText(c)} className="rounded-full border border-border-subtle bg-white/[0.02] px-2.5 py-1 text-[11px] text-ink-muted hover:bg-white/[0.05]">
                    {c}
                  </button>
                ))}
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Switch checked={autoExecute} onCheckedChange={setAutoExecute} />
                  <span className="text-xs text-ink-secondary">Auto-execute on the real allocation engine</span>
                </div>
                <Button onClick={onSendCommand} disabled={command.isPending}>
                  <Send className="h-3.5 w-3.5" /> {command.isPending ? "Parsing..." : "Send"}
                </Button>
              </div>

              {command.data && (
                <div className="space-y-3 rounded-xl border border-border-subtle bg-white/[0.02] p-4">
                  <p className="text-sm text-ink-secondary">{command.data.message}</p>
                  <div className="flex flex-wrap gap-1.5">
                    <Badge>{command.data.parsed.algorithm}</Badge>
                    {command.data.parsed.department_filter && <Badge variant="secondary">Dept: {command.data.parsed.department_filter}</Badge>}
                    {command.data.parsed.year_filter && <Badge variant="secondary">Year: {command.data.parsed.year_filter}</Badge>}
                    <Badge variant="secondary">{command.data.matched_student_count} students matched</Badge>
                    <Badge variant="secondary">{command.data.matched_lab_count} labs matched</Badge>
                    {command.data.executed && <Badge variant="success">Executed as Run #{command.data.run_id}</Badge>}
                  </div>
                  <ul className="space-y-1 text-xs text-ink-muted">
                    {command.data.parsed.notes.map((n, i) => <li key={i}>• {n}</li>)}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ask">
          <Card>
            <CardHeader>
              <CardTitle>Ask about the latest run</CardTitle>
              <CardDescription>Answers are computed from real allocation records, never fabricated.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex gap-2">
                <Input placeholder="Why are 12 students unmatched?" value={question} onChange={(e) => setQuestion(e.target.value)} />
                <Button onClick={onAskQuestion} disabled={analyticsQuery.isPending}>
                  <MessageSquareQuote className="h-3.5 w-3.5" /> Ask
                </Button>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {EXAMPLE_QUESTIONS.map((q) => (
                  <button key={q} onClick={() => setQuestion(q)} className="rounded-full border border-border-subtle bg-white/[0.02] px-2.5 py-1 text-[11px] text-ink-muted hover:bg-white/[0.05]">
                    {q}
                  </button>
                ))}
              </div>
              {analyticsQuery.data && (
                <div className="rounded-xl border border-border-subtle bg-white/[0.02] p-4 text-sm text-ink-secondary">
                  {analyticsQuery.data.answer}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="conflicts">
          <Card>
            <CardHeader>
              <CardTitle>Detected Conflicts</CardTitle>
              <CardDescription>Deterministic checks over real capacity, availability and department-supply data.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {conflictsLoading ? (
                <Skeleton className="h-24 w-full" />
              ) : !conflicts?.length ? (
                <p className="py-6 text-center text-xs text-ink-muted">No conflicts detected.</p>
              ) : (
                conflicts.map((c, i) => (
                  <div key={i} className="flex items-start gap-2 rounded-lg border border-warning/20 bg-warning/[0.05] p-3 text-xs">
                    <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" />
                    <div>
                      <Badge variant="warning" className="mb-1">{c.type}</Badge>
                      <p className="text-ink-secondary">{c.message}</p>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="report">
          <Card>
            <CardHeader>
              <CardTitle>Automatic Report</CardTitle>
              <CardDescription>Generated entirely from stored run statistics.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="secondary" onClick={() => report.refetch()}>
                <FileText className="h-3.5 w-3.5" /> Generate Report
              </Button>
              {report.isFetching ? (
                <Skeleton className="h-48 w-full" />
              ) : report.data ? (
                <pre className="whitespace-pre-wrap rounded-xl border border-border-subtle bg-white/[0.02] p-4 text-xs text-ink-secondary">{report.data}</pre>
              ) : null}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
