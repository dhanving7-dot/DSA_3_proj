import { useState } from "react"
import { useSearchParams } from "react-router-dom"
import { toast } from "sonner"
import { Plus, Pencil, Trash2, Settings2, FlaskConical } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/common/EmptyState"
import { LabFormDialog } from "@/components/labs/LabFormDialog"
import { LabDetailDialog } from "@/components/labs/LabDetailDialog"
import { useDeleteLab, useLabs } from "@/hooks/useLabs"
import { apiErrorMessage } from "@/lib/api"
import type { Laboratory } from "@/types"

const STATUS_VARIANT: Record<string, "success" | "warning" | "critical"> = {
  ACTIVE: "success",
  MAINTENANCE: "warning",
  INACTIVE: "critical",
}

export default function LabsPage() {
  const { data: labs, isLoading } = useLabs()
  const deleteLab = useDeleteLab()
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Laboratory | null>(null)
  const [params] = useSearchParams()
  const focus = Number(params.get("focus")) || null
  const [detailId, setDetailId] = useState<number | null>(focus)
  // the command palette deep-links here with ?focus=<lab id>; open that lab whenever the URL changes
  const [seenFocus, setSeenFocus] = useState(focus)
  if (focus !== seenFocus) {
    setSeenFocus(focus)
    if (focus) setDetailId(focus)
  }

  const detailLab = labs?.find((l) => l.id === detailId) ?? null

  async function onDelete(id: number) {
    if (!confirm("Delete this laboratory? This cannot be undone.")) return
    try {
      await deleteLab.mutateAsync(id)
      toast.success("Laboratory deleted")
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-ink-muted">{labs?.length ?? 0} laboratories registered</p>
        <Button size="sm" onClick={() => { setEditing(null); setFormOpen(true) }}>
          <Plus className="h-3.5 w-3.5" /> Add Laboratory
        </Button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-40" />)}
        </div>
      ) : !labs?.length ? (
        <EmptyState icon={FlaskConical} title="No laboratories yet" description="Add your first laboratory to start building allocation graphs." />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {labs.map((lab) => (
            <Card key={lab.id} className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-ink">{lab.name}</p>
                  <p className="text-xs text-ink-muted">{lab.code} · {lab.department}</p>
                </div>
                <Badge variant={STATUS_VARIANT[lab.status]}>{lab.status}</Badge>
              </div>
              <div className="mt-3 flex items-center gap-4 text-xs text-ink-secondary">
                <span>Capacity: <span className="tabular text-ink">{lab.capacity}</span></span>
                <span>{lab.required_skills.length} skill req.</span>
                <span>{lab.equipment.length} equipment</span>
              </div>
              {lab.location && <p className="mt-1 text-xs text-ink-muted">{lab.location}</p>}
              <div className="mt-4 flex justify-end gap-1">
                <Button size="icon" variant="ghost" onClick={() => setDetailId(lab.id)}><Settings2 className="h-3.5 w-3.5" /></Button>
                <Button size="icon" variant="ghost" onClick={() => { setEditing(lab); setFormOpen(true) }}><Pencil className="h-3.5 w-3.5" /></Button>
                <Button size="icon" variant="ghost" onClick={() => onDelete(lab.id)}><Trash2 className="h-3.5 w-3.5 text-critical" /></Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <LabFormDialog open={formOpen} onOpenChange={setFormOpen} lab={editing} />
      <LabDetailDialog lab={detailLab} onOpenChange={(open) => !open && setDetailId(null)} />
    </div>
  )
}
