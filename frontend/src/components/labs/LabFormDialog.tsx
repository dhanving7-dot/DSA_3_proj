import { useEffect, useState } from "react"
import { toast } from "sonner"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useCreateLab, useUpdateLab } from "@/hooks/useLabs"
import { apiErrorMessage } from "@/lib/api"
import type { Laboratory, LabStatus } from "@/types"

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  lab?: Laboratory | null
}

const EMPTY = { code: "", name: "", department: "CSE", capacity: 20, location: "", status: "ACTIVE" as LabStatus }

export function LabFormDialog({ open, onOpenChange, lab }: Props) {
  const [form, setForm] = useState(EMPTY)
  const create = useCreateLab()
  const update = useUpdateLab()
  const isEdit = !!lab

  useEffect(() => {
    if (lab) {
      setForm({ code: lab.code, name: lab.name, department: lab.department, capacity: lab.capacity, location: lab.location, status: lab.status })
    } else {
      setForm(EMPTY)
    }
  }, [lab, open])

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    try {
      if (isEdit && lab) {
        await update.mutateAsync({ id: lab.id, payload: form })
        toast.success("Laboratory updated")
      } else {
        await create.mutateAsync(form)
        toast.success("Laboratory created")
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
          <DialogTitle>{isEdit ? "Edit Laboratory" : "Add Laboratory"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label>Code</Label>
              <Input required disabled={isEdit} value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
            </div>
            <div className="space-y-1">
              <Label>Name</Label>
              <Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label>Department</Label>
              <Input required value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} />
            </div>
            <div className="space-y-1">
              <Label>Capacity</Label>
              <Input type="number" min={0} required value={form.capacity} onChange={(e) => setForm({ ...form, capacity: Number(e.target.value) })} />
            </div>
          </div>
          <div className="space-y-1">
            <Label>Location</Label>
            <Input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
          </div>
          <div className="space-y-1">
            <Label>Status</Label>
            <Select value={form.status} onValueChange={(v) => setForm({ ...form, status: v as LabStatus })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="ACTIVE">Active</SelectItem>
                <SelectItem value="INACTIVE">Inactive</SelectItem>
                <SelectItem value="MAINTENANCE">Maintenance</SelectItem>
              </SelectContent>
            </Select>
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
