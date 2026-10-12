import { useRef, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { toast } from "sonner"
import { Plus, Search, Upload, Download, Pencil, Trash2, Settings2, Users } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/common/EmptyState"
import { StudentFormDialog } from "@/components/students/StudentFormDialog"
import { StudentDetailDialog } from "@/components/students/StudentDetailDialog"
import { useDeleteStudent, useImportStudentsCsv, useStudents, downloadStudentsCsv } from "@/hooks/useStudents"
import { apiErrorMessage } from "@/lib/api"
import type { Student } from "@/types"

const DEPARTMENTS = ["CSE", "ECE", "EEE", "MECH", "CIVIL", "IT", "AIML"]

export default function StudentsPage() {
  const [params] = useSearchParams()
  const urlSearch = params.get("search")
  const [search, setSearch] = useState(urlSearch ?? "")
  // the command palette deep-links here with ?search=<name>; adopt a new value whenever the URL changes
  const [seenUrlSearch, setSeenUrlSearch] = useState(urlSearch)
  if (urlSearch !== seenUrlSearch) {
    setSeenUrlSearch(urlSearch)
    if (urlSearch != null) setSearch(urlSearch)
  }
  const [department, setDepartment] = useState<string>("")
  const [year, setYear] = useState<string>("")
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Student | null>(null)
  const [detailId, setDetailId] = useState<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: students, isLoading } = useStudents({
    search: search || undefined,
    department: department || undefined,
    year: year ? Number(year) : undefined,
  })
  const deleteStudent = useDeleteStudent()
  const importCsv = useImportStudentsCsv()

  const detailStudent = students?.find((s) => s.id === detailId) ?? null

  async function onDelete(id: number) {
    if (!confirm("Delete this student? This cannot be undone.")) return
    try {
      await deleteStudent.mutateAsync(id)
      toast.success("Student deleted")
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  async function onImportFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const result = await importCsv.mutateAsync(file)
      toast.success(`Imported ${result.created} students${result.errors.length ? ` (${result.errors.length} row errors)` : ""}`)
    } catch (err) {
      toast.error(apiErrorMessage(err))
    } finally {
      e.target.value = ""
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-muted" />
          <Input placeholder="Search roll number, name or email..." className="pl-8" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <Select value={department} onValueChange={(v) => setDepartment(v === "all" ? "" : v)}>
          <SelectTrigger className="w-36"><SelectValue placeholder="Department" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Departments</SelectItem>
            {DEPARTMENTS.map((d) => <SelectItem key={d} value={d}>{d}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={year} onValueChange={(v) => setYear(v === "all" ? "" : v)}>
          <SelectTrigger className="w-28"><SelectValue placeholder="Year" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Years</SelectItem>
            {[1, 2, 3, 4].map((y) => <SelectItem key={y} value={String(y)}>Year {y}</SelectItem>)}
          </SelectContent>
        </Select>

        <input ref={fileInputRef} type="file" accept=".csv" hidden onChange={onImportFile} />
        <Button variant="secondary" size="sm" onClick={() => fileInputRef.current?.click()}>
          <Upload className="h-3.5 w-3.5" /> Import CSV
        </Button>
        <Button variant="secondary" size="sm" onClick={() => downloadStudentsCsv().catch((e) => toast.error(apiErrorMessage(e)))}>
          <Download className="h-3.5 w-3.5" /> Export CSV
        </Button>
        <Button size="sm" onClick={() => { setEditing(null); setFormOpen(true) }}>
          <Plus className="h-3.5 w-3.5" /> Add Student
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
        </div>
      ) : !students?.length ? (
        <EmptyState icon={Users} title="No students found" description="Try adjusting your filters or add a new student." />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Roll No.</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Department</TableHead>
              <TableHead>Year</TableHead>
              <TableHead>CGPA</TableHead>
              <TableHead>Skills</TableHead>
              <TableHead>Preferences</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {students.map((s) => (
              <TableRow key={s.id}>
                <TableCell className="font-mono text-xs text-ink">{s.roll_number}</TableCell>
                <TableCell className="text-ink">{s.full_name}</TableCell>
                <TableCell><Badge variant="secondary">{s.department}</Badge></TableCell>
                <TableCell>{s.year}</TableCell>
                <TableCell className="tabular">{s.cgpa.toFixed(2)}</TableCell>
                <TableCell>{s.skills.length}</TableCell>
                <TableCell>{s.preferences.length}</TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button size="icon" variant="ghost" onClick={() => setDetailId(s.id)}><Settings2 className="h-3.5 w-3.5" /></Button>
                    <Button size="icon" variant="ghost" onClick={() => { setEditing(s); setFormOpen(true) }}><Pencil className="h-3.5 w-3.5" /></Button>
                    <Button size="icon" variant="ghost" onClick={() => onDelete(s.id)}><Trash2 className="h-3.5 w-3.5 text-critical" /></Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <StudentFormDialog open={formOpen} onOpenChange={setFormOpen} student={editing} />
      <StudentDetailDialog student={detailStudent} onOpenChange={(open) => !open && setDetailId(null)} />
    </div>
  )
}
