import { useNavigate } from "react-router-dom"
import { Search, LogOut, User as UserIcon } from "lucide-react"
import { useAuthStore } from "@/store/authStore"
import { useUIStore } from "@/store/uiStore"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { initials } from "@/lib/utils"

export function Topbar({ title }: { title: string }) {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const setCommandPaletteOpen = useUIStore((s) => s.setCommandPaletteOpen)
  const navigate = useNavigate()

  return (
    <header className="flex h-16 items-center justify-between border-b border-border-subtle bg-canvas/80 px-6 backdrop-blur">
      <h1 className="text-lg font-semibold text-ink">{title}</h1>

      <div className="flex items-center gap-3">
        <button
          onClick={() => setCommandPaletteOpen(true)}
          className="flex items-center gap-2 rounded-lg border border-border-subtle bg-white/[0.03] px-3 py-1.5 text-xs text-ink-muted transition-colors hover:bg-white/[0.06]"
        >
          <Search className="h-3.5 w-3.5" />
          Search
          <kbd className="rounded border border-border-subtle px-1 text-[10px]">⌘K</kbd>
        </button>

        <DropdownMenu>
          <DropdownMenuTrigger className="outline-none">
            <Avatar>
              <AvatarFallback>{user ? initials(user.full_name) : <UserIcon className="h-4 w-4" />}</AvatarFallback>
            </Avatar>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>
              <p className="text-ink">{user?.full_name}</p>
              <p className="text-[10px] text-ink-muted">{user?.email}</p>
            </DropdownMenuLabel>
            <div className="px-2 pb-1">
              <Badge variant="secondary">{user?.role}</Badge>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onSelect={() => {
                logout()
                navigate("/login")
              }}
              className="text-critical"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
