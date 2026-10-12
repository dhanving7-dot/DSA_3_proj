import { useEffect, useState } from "react"
import { toast } from "sonner"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useCreateStudent, useUpdateStudent } from "@/hooks/useStudents"
import { apiErrorMessage } from "@/lib/api"
import type { Student } from "@/types"

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  student?: Student | null
}

const EMPTY = {
  roll_number: "",
  full_name: "",
  email: "",
  department: "CSE",
  year: 1,
  cgpa: 0,
  priority_score: 0,
}

export function StudentFormDialog({ open, onOpenChange, student }: Props) {
  const [form, setForm] = useState(EMPTY)
  const create = useCreateStudent()
  const update = useUpdateStudent()
  const isEdit = !!student

  useEffect(() => {
    if (student) {
      setForm({
        roll_number: student.roll_number,
        full_name: student.full_name,
        email: student.email,
        department: student.department,
        year: student.year,
        cgpa: student.cgpa,
        priority_score: student.priority_score,
      })
    } else {
      setForm(EMPTY)
    }
  }, [student, open])

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    try {
      if (isEdit && student) {
        await update.mutateAsync({ id: student.id, payload: form })
        toast.success("Student updated")
      } else {
        await create.mutateAsync(form)
        toast.success("Student created")
      }
      onOpenChange(false)
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  const pending = create.isPending || update.isPending

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Student" : "Add Student"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label>Roll Number</Label>
              <Input required disabled={isEdit} value={form.roll_number} onChange={(e) => setForm({ ...form, roll_number: e.target.value })} />
            </div>
            <div className="space-y-1">
              <Label>Full Name</Label>
              <Input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            </div>
          </div>
          <div className="space-y-1">
            <Label>Email</Label>
            <Input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="space-y-1">
              <Label>Department</Label>
              <Input required value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} />
            </div>
            <div className="space-y-1">
              <Label>Year</Label>
              <Input type="number" min={1} max={5} required value={form.year} onChange={(e) => setForm({ ...form, year: Number(e.target.value) })} />
            </div>
            <div className="space-y-1">
              <Label>CGPA</Label>
              <Input type="number" step="0.01" min={0} max={10} value={form.cgpa} onChange={(e) => setForm({ ...form, cgpa: Number(e.target.value) })} />
            </div>
          </div>
          <div className="space-y-1">
            <Label>Priority Score (0-1, used for fairness weighting)</Label>
            <Input type="number" step="0.01" min={0} max={1} value={form.priority_score} onChange={(e) => setForm({ ...form, priority_score: Number(e.target.value) })} />
          </div>
          <DialogFooter className="pt-2">
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={pending}>{pending ? "Saving..." : "Save"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
