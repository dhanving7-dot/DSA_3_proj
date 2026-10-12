import { useState } from "react"
import { toast } from "sonner"
import { Plus, Trash2 } from "lucide-react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useAddSkill, useRemoveSkill, useSetPreferences } from "@/hooks/useStudents"
import { useLabs } from "@/hooks/useLabs"
import { apiErrorMessage } from "@/lib/api"
import type { Student } from "@/types"

export function StudentDetailDialog({ student, onOpenChange }: { student: Student | null; onOpenChange: (open: boolean) => void }) {
  const [skillName, setSkillName] = useState("")
  const [proficiency, setProficiency] = useState(3)
  const [newLabId, setNewLabId] = useState<string>("")
  const [newRank, setNewRank] = useState(1)

  const { data: labs = [] } = useLabs()
  const addSkill = useAddSkill()
  const removeSkill = useRemoveSkill()
  const setPreferences = useSetPreferences()

  if (!student) return null
  const current = student

  async function onAddSkill() {
    if (!skillName.trim()) return
    try {
      await addSkill.mutateAsync({ studentId: current.id, skill_name: skillName.trim(), proficiency_level: proficiency })
      setSkillName("")
      toast.success("Skill added")
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  async function onAddPreference() {
    if (!newLabId) return
    const existing = current.preferences.map((p) => ({ lab_id: p.lab_id, rank: p.rank }))
    if (existing.some((p) => p.lab_id === Number(newLabId) || p.rank === newRank)) {
      toast.error("That lab or rank is already used in this student's preference list")
      return
    }
    try {
      await setPreferences.mutateAsync({
        studentId: current.id,
        preferences: [...existing, { lab_id: Number(newLabId), rank: newRank }],
      })
      setNewLabId("")
      toast.success("Preference added")
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  async function onRemovePreference(labId: number) {
    const remaining = current.preferences.filter((p) => p.lab_id !== labId).map((p) => ({ lab_id: p.lab_id, rank: p.rank }))
    try {
      await setPreferences.mutateAsync({ studentId: current.id, preferences: remaining })
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  return (
    <Dialog open={!!student} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{student.full_name}</DialogTitle>
          <p className="text-xs text-ink-muted">{student.roll_number} · {student.department} · Year {student.year}</p>
        </DialogHeader>

        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-muted">Skills</p>
          <div className="mb-3 flex flex-wrap gap-1.5">
            {student.skills.length === 0 && <p className="text-xs text-ink-muted">No skills recorded yet.</p>}
            {student.skills.map((s) => (
              <Badge key={s.id} variant="secondary" className="gap-1.5">
                {s.skill_name} · L{s.proficiency_level}
                <button onClick={() => removeSkill.mutate({ studentId: student.id, skillId: s.id })}>
                  <Trash2 className="h-3 w-3 text-ink-muted hover:text-critical" />
                </button>
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Input placeholder="Skill name" value={skillName} onChange={(e) => setSkillName(e.target.value)} className="flex-1" />
            <Input type="number" min={1} max={5} value={proficiency} onChange={(e) => setProficiency(Number(e.target.value))} className="w-16" />
            <Button size="icon" variant="secondary" onClick={onAddSkill}><Plus className="h-4 w-4" /></Button>
          </div>
        </div>

        <Separator />

        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-muted">Lab Preferences (ranked)</p>
          <div className="mb-3 space-y-1.5">
            {student.preferences.length === 0 && <p className="text-xs text-ink-muted">No preferences recorded yet.</p>}
            {[...student.preferences].sort((a, b) => a.rank - b.rank).map((p) => {
              const lab = labs.find((l) => l.id === p.lab_id)
              return (
                <div key={p.id} className="flex items-center justify-between rounded-lg border border-border-subtle bg-white/[0.02] px-3 py-1.5 text-xs">
                  <span className="text-ink-secondary">#{p.rank} · {lab?.name ?? `Lab ${p.lab_id}`}</span>
                  <button onClick={() => onRemovePreference(p.lab_id)}>
                    <Trash2 className="h-3.5 w-3.5 text-ink-muted hover:text-critical" />
                  </button>
                </div>
              )
            })}
          </div>
          <div className="flex gap-2">
            <Select value={newLabId} onValueChange={setNewLabId}>
              <SelectTrigger className="flex-1"><SelectValue placeholder="Choose laboratory" /></SelectTrigger>
              <SelectContent>
                {labs.map((l) => (
                  <SelectItem key={l.id} value={String(l.id)}>{l.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input type="number" min={1} value={newRank} onChange={(e) => setNewRank(Number(e.target.value))} className="w-16" />
            <Button size="icon" variant="secondary" onClick={onAddPreference}><Plus className="h-4 w-4" /></Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
