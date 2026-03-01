import { useAllScorecards } from './useScorecards'
import type { ScorecardResult } from './api'
import { cn } from '@/lib/utils/cn'

const LEVEL_COLOR: Record<string, string> = {
  platinum: 'bg-cyan-500/10 text-cyan-500',
  gold: 'bg-yellow-500/10 text-yellow-500',
  silver: 'bg-slate-400/10 text-slate-400',
  bronze: 'bg-orange-500/10 text-orange-500',
  failing: 'bg-red-500/10 text-red-500',
}

const LEVEL_EMOJI: Record<string, string> = {
  platinum: '🏆',
  gold: '🥇',
  silver: '🥈',
  bronze: '🥉',
  failing: '❌',
}

function ServiceRow({ result }: { result: ScorecardResult }) {
  return (
    <div className="flex items-center gap-4 py-3 border-b border-border last:border-0">
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm truncate">{result.entity_name}</p>
        <p className="text-xs text-muted-foreground mt-0.5">{result.template_name}</p>
      </div>

      {/* Score bar */}
      <div className="flex items-center gap-3 w-48">
        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
          <div
            className={cn(
              'h-full rounded-full',
              result.percentage >= 75 ? 'bg-green-500' :
              result.percentage >= 50 ? 'bg-yellow-500' : 'bg-red-500',
            )}
            style={{ width: `${result.percentage}%` }}
          />
        </div>
        <span className="text-xs font-semibold tabular-nums w-10 text-right">
          {result.percentage.toFixed(0)}%
        </span>
      </div>

      {/* Level badge */}
      <span className={cn('text-xs font-medium px-2 py-1 rounded-full flex-shrink-0', LEVEL_COLOR[result.level])}>
        {LEVEL_EMOJI[result.level]} {result.level.charAt(0).toUpperCase() + result.level.slice(1)}
      </span>
    </div>
  )
}

// Group results by service, picking worst level
function buildLeaderboard(results: ScorecardResult[]): ScorecardResult[] {
  const LEVELS = ['failing', 'bronze', 'silver', 'gold', 'platinum']
  const byService = new Map<string, ScorecardResult[]>()
  for (const r of results) {
    const list = byService.get(r.entity_id) ?? []
    list.push(r)
    byService.set(r.entity_id, list)
  }
  return Array.from(byService.values())
    .map(group => group.reduce((worst, r) =>
      LEVELS.indexOf(r.level) < LEVELS.indexOf(worst.level) ? r : worst
    ))
    .sort((a, b) => b.percentage - a.percentage)
}

export function ScorecardsPage() {
  const { data: results, isLoading } = useAllScorecards()
  const leaderboard = results ? buildLeaderboard(results) : []

  const levelCounts = leaderboard.reduce<Record<string, number>>((acc, r) => {
    acc[r.level] = (acc[r.level] ?? 0) + 1
    return acc
  }, {})

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Scorecards</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Production readiness and security posture across all services
        </p>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {(['platinum', 'gold', 'silver', 'bronze', 'failing'] as const).map(level => (
          <div key={level} className={cn('rounded-xl p-4 border', LEVEL_COLOR[level], 'border-current/20')}>
            <p className="text-xs font-medium opacity-70 capitalize">{level}</p>
            <p className="text-2xl font-bold mt-1">{levelCounts[level] ?? 0}</p>
          </div>
        ))}
      </div>

      {/* Leaderboard */}
      <div className="bg-card border border-border rounded-xl p-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">
          Service Leaderboard (best score per service)
        </h2>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-10 bg-muted rounded animate-pulse" />
            ))}
          </div>
        ) : leaderboard.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4">No scorecard data available yet.</p>
        ) : (
          leaderboard.map(r => <ServiceRow key={r.entity_id} result={r} />)
        )}
      </div>

      {/* All results grouped by template */}
      {results && results.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            All Results by Template
          </h2>
          {Array.from(new Set(results.map(r => r.template_name))).map(tplName => {
            const group = results.filter(r => r.template_name === tplName)
            return (
              <div key={tplName} className="bg-card border border-border rounded-xl p-4">
                <h3 className="font-semibold mb-3">{tplName}</h3>
                {group.map(r => <ServiceRow key={`${r.entity_id}-${r.template_id}`} result={r} />)}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
