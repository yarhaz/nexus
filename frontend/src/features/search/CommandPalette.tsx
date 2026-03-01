import { useEffect, useState } from 'react'
import { Command } from 'cmdk'
import { useNavigate } from '@tanstack/react-router'
import {
  Search,
  LayoutDashboard,
  BookOpen,
  LogOut,
  Zap,
  Cloud,
  Layers,
  Users,
  Globe,
  Package,
  AlertTriangle,
  ClipboardList,
  Server,
  Loader2,
} from 'lucide-react'
import { useMsal } from '@azure/msal-react'
import { useAuthStore } from '@/features/auth/authStore'
import { useSearch } from './useSearch'

const entityIcon: Record<string, React.ElementType> = {
  Service: Server,
  AzureResource: Cloud,
  Environment: Layers,
  Team: Users,
  ApiEndpoint: Globe,
  Package: Package,
  Incident: AlertTriangle,
  ADOWorkItem: ClipboardList,
}

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const navigate = useNavigate()
  const { instance } = useMsal()
  const { clear } = useAuthStore()

  const { data: searchData, isFetching } = useSearch(input)

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if ((e.key === 'k' && (e.metaKey || e.ctrlKey)) || e.key === '/') {
        e.preventDefault()
        setOpen((o) => !o)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  // Reset input on close
  useEffect(() => {
    if (!open) setInput('')
  }, [open])

  const runCommand = (fn: () => void) => {
    setOpen(false)
    fn()
  }

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 bg-black/50 flex items-start justify-center pt-[20vh]"
      onClick={() => setOpen(false)}
    >
      <div
        className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-lg overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <Command shouldFilter={false}>
          <div className="flex items-center border-b border-border px-3">
            <Search className="w-4 h-4 text-muted-foreground mr-2 flex-shrink-0" />
            <Command.Input
              value={input}
              onValueChange={setInput}
              placeholder="Search catalog or run a command..."
              className="flex-1 py-3 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            />
            {isFetching && <Loader2 className="w-4 h-4 text-muted-foreground animate-spin mr-2" />}
            <kbd className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">Esc</kbd>
          </div>

          <Command.List className="p-2 max-h-96 overflow-y-auto">
            <Command.Empty className="text-center text-muted-foreground text-sm py-6">
              {input.length >= 2 ? 'No results found.' : 'Type to search the catalog…'}
            </Command.Empty>

            {/* Catalog search results */}
            {searchData && searchData.hits.length > 0 && (
              <Command.Group heading={`Catalog — ${searchData.total} result${searchData.total !== 1 ? 's' : ''}`}>
                {searchData.hits.map((hit) => {
                  const Icon = entityIcon[hit.entity_type] ?? Server
                  return (
                    <Command.Item
                      key={hit.id}
                      value={hit.id}
                      onSelect={() => runCommand(() => navigate({ to: '/catalog/$entityId', params: { entityId: hit.id } }))}
                      className="flex items-center gap-3 px-2 py-2 rounded cursor-pointer hover:bg-muted text-sm"
                    >
                      <Icon className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                      <div className="min-w-0">
                        <span className="font-medium truncate block">{hit.name}</span>
                        {hit.description && (
                          <span className="text-xs text-muted-foreground truncate block">{hit.description}</span>
                        )}
                      </div>
                      <span className="ml-auto text-xs text-muted-foreground flex-shrink-0">{hit.entity_type}</span>
                    </Command.Item>
                  )
                })}
              </Command.Group>
            )}

            {/* Navigation commands */}
            <Command.Group heading="Navigation">
              <Command.Item
                onSelect={() => runCommand(() => navigate({ to: '/dashboard' }))}
                className="flex items-center gap-2 px-2 py-2 rounded cursor-pointer hover:bg-muted text-sm"
              >
                <LayoutDashboard className="w-4 h-4" /> Dashboard
              </Command.Item>
              <Command.Item
                onSelect={() => runCommand(() => navigate({ to: '/catalog' }))}
                className="flex items-center gap-2 px-2 py-2 rounded cursor-pointer hover:bg-muted text-sm"
              >
                <BookOpen className="w-4 h-4" /> Catalog
              </Command.Item>
              <Command.Item
                onSelect={() => runCommand(() => navigate({ to: '/actions' }))}
                className="flex items-center gap-2 px-2 py-2 rounded cursor-pointer hover:bg-muted text-sm"
              >
                <Zap className="w-4 h-4" /> Actions
              </Command.Item>
            </Command.Group>

            <Command.Group heading="Account">
              <Command.Item
                onSelect={() =>
                  runCommand(() => {
                    clear()
                    instance.logoutRedirect()
                  })
                }
                className="flex items-center gap-2 px-2 py-2 rounded cursor-pointer hover:bg-muted text-sm text-destructive"
              >
                <LogOut className="w-4 h-4" /> Sign out
              </Command.Item>
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  )
}
