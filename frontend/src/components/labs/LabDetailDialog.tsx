import { useState } from "react"
import { toast } from "sonner"
import { Plus } from "lucide-react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { useAddLabEquipment, useAddLabSkill, useAddLabTimeSlot } from "@/hooks/useLabs"
import { apiErrorMessage } from "@/lib/api"
import type { Laboratory } from "@/types"

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

export function LabDetailDialog({ lab, onOpenChange }: { lab: Laboratory | null; onOpenChange: (open: boolean) => void }) {
  const [skillName, setSkillName] = useState("")
  const [minProf, setMinProf] = useState(2)
  const [equipName, setEquipName] = useState("")
  const [equipQty, setEquipQty] = useState(1)
  const [day, setDay] = useState(0)
  const [start, setStart] = useState("09:00")
  const [end, setEnd] = useState("11:00")

  const addSkill = useAddLabSkill()
  const addEquipment = useAddLabEquipment()
  const addSlot = useAddLabTimeSlot()

  if (!lab) return null
  const current = lab

  async function onAddSkill() {
    if (!skillName.trim()) return
    try {
      await addSkill.mutateAsync({ labId: current.id, skill_name: skillName.trim(), min_proficiency: minProf, required: true })
      setSkillName("")
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  async function onAddEquipment() {
    if (!equipName.trim()) return
    try {
      await addEquipment.mutateAsync({ labId: current.id, equipment_name: equipName.trim(), quantity: equipQty })
      setEquipName("")
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  async function onAddSlot() {
    try {
      await addSlot.mutateAsync({ labId: current.id, day_of_week: day, start_time: start, end_time: end, is_available: true })
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  return (
    <Dialog open={!!lab} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{lab.name}</DialogTitle>
          <p className="text-xs text-ink-muted">{lab.code} · {lab.department} · Capacity {lab.capacity}</p>
        </DialogHeader>

        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-muted">Required Skills</p>
          <div className="mb-3 flex flex-wrap gap-1.5">
            {lab.required_skills.length === 0 && <p className="text-xs text-ink-muted">No specific skill requirements.</p>}
            {lab.required_skills.map((s) => (
              <Badge key={s.id} variant="secondary">{s.skill_name} · min L{s.min_proficiency}</Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Input placeholder="Skill name" value={skillName} onChange={(e) => setSkillName(e.target.value)} className="flex-1" />
            <Input type="number" min={1} max={5} value={minProf} onChange={(e) => setMinProf(Number(e.target.value))} className="w-16" />
            <Button size="icon" variant="secondary" onClick={onAddSkill}><Plus className="h-4 w-4" /></Button>
          </div>
        </div>

        <Separator />

        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-muted">Equipment</p>
          <div className="mb-3 flex flex-wrap gap-1.5">
            {lab.equipment.length === 0 && <p className="text-xs text-ink-muted">No equipment recorded.</p>}
            {lab.equipment.map((e) => (
              <Badge key={e.id} variant="secondary">{e.equipment_name} × {e.quantity}</Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Input placeholder="Equipment name" value={equipName} onChange={(e) => setEquipName(e.target.value)} className="flex-1" />
            <Input type="number" min={0} value={equipQty} onChange={(e) => setEquipQty(Number(e.target.value))} className="w-16" />
            <Button size="icon" variant="secondary" onClick={onAddEquipment}><Plus className="h-4 w-4" /></Button>
          </div>
        </div>

        <Separator />

        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-muted">Availability / Time Slots</p>
          <div className="mb-3 flex flex-wrap gap-1.5">
            {lab.time_slots.length === 0 && <p className="text-xs text-ink-muted">No time slots recorded (treated as always available).</p>}
            {lab.time_slots.map((t) => (
              <Badge key={t.id} variant={t.is_available ? "success" : "critical"}>
                {DAYS[t.day_of_week]} {t.start_time}-{t.end_time}
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <select value={day} onChange={(e) => setDay(Number(e.target.value))} className="rounded-lg border border-border-strong bg-white/[0.03] px-2 text-xs text-ink">
              {DAYS.map((d, i) => <option key={d} value={i}>{d}</option>)}
            </select>
            <Input type="time" value={start} onChange={(e) => setStart(e.target.value)} className="w-24" />
            <Input type="time" value={end} onChange={(e) => setEnd(e.target.value)} className="w-24" />
            <Button size="icon" variant="secondary" onClick={onAddSlot}><Plus className="h-4 w-4" /></Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
