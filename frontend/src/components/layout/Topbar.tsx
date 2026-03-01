import { Sun, Moon, Monitor, LogOut, Search } from 'lucide-react'
import { useMsal } from '@azure/msal-react'
import { useTheme } from './ThemeProvider'
import { useAuthStore } from '@/features/auth/authStore'
import { cn } from '@/lib/utils/cn'

export function Topbar() {
  const { theme, setTheme } = useTheme()
  const { instance } = useMsal()
  const { user, clear } = useAuthStore()

  const cycleTheme = () => {
    const themes = ['light', 'dark', 'system'] as const
    const idx = themes.indexOf(theme as typeof themes[number])
    setTheme(themes[(idx + 1) % themes.length])
  }

  const ThemeIcon = theme === 'light' ? Sun : theme === 'dark' ? Moon : Monitor

  return (
    <header className="h-16 border-b border-border flex items-center justify-between px-6 bg-card flex-shrink-0">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Search className="w-4 h-4" />
        <span>Press <kbd className="bg-muted text-foreground text-xs px-1.5 py-0.5 rounded font-mono">⌘K</kbd> to search</span>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={cycleTheme}
          className="w-9 h-9 flex items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          aria-label="Toggle theme"
        >
          <ThemeIcon className="w-4 h-4" />
        </button>

        {user && (
          <div className="flex items-center gap-2 ml-2">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
              <span className="text-xs font-semibold text-primary">
                {user.name?.[0]?.toUpperCase() ?? '?'}
              </span>
            </div>
            <span className="text-sm text-foreground hidden md:block">{user.name}</span>
          </div>
        )}

        <button
          onClick={() => { clear(); instance.logoutRedirect() }}
          className="w-9 h-9 flex items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-destructive transition-colors"
          aria-label="Sign out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  )
}
