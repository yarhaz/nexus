import { CheckCircle, XCircle, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { useServiceScorecard } from './useScorecards'
import type { ScorecardResult, RuleResult } from './api'
import { cn } from '@/lib/utils/cn'

const LEVEL_COLOR: Record<string, string> = {
  platinum: 'text-cyan-500 bg-cyan-500/10 border-cyan-500/20',
  gold: 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20',
  silver: 'text-slate-400 bg-slate-400/10 border-slate-400/20',
  bronze: 'text-orange-500 bg-orange-500/10 border-orange-500/20',
  failing: 'text-red-500 bg-red-500/10 border-red-500/20',
}

const LEVEL_LABEL: Record<string, string> = {
  platinum: '🏆 Platinum',
  gold: '🥇 Gold',
  silver: '🥈 Silver',
  bronze: '🥉 Bronze',
  failing: '❌ Failing',
}

function RuleRow({ rule }: { rule: RuleResult }) {
  return (
    <div className="flex items-start gap-3 py-2 border-b border-border last:border-0">
      {rule.passed ? (
        <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
      ) : (
        <XCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
      )}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{rule.rule_name}</p>
        <p className="text-xs text-muted-foreground mt-0.5">{rule.reason}</p>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className="text-xs text-muted-foreground">×{rule.weight}</span>
        {!rule.passed && rule.remedy_url && (
          <a
            href={rule.remedy_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-primary flex items-center gap-1 hover:underline"
          >
            Fix <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>
    </div>
  )
}

function ScoreCard({ result }: { result: ScorecardResult }) {
  const [expanded, setExpanded] = useState(false)
  const passedCount = result.rules.filter(r => r.passed).length

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      <button
        className="w-full flex items-center gap-4 p-4 hover:bg-muted/50 transition-colors"
        onClick={() => setExpanded(e => !e)}
      >
        {/* Level badge */}
        <span className={cn('text-xs font-semibold px-2 py-1 rounded-full border', LEVEL_COLOR[result.level])}>
          {LEVEL_LABEL[result.level]}
        </span>

        {/* Template name */}
        <span className="flex-1 text-left font-medium text-sm">{result.template_name}</span>

        {/* Score bar */}
        <div className="flex items-center gap-3">
          <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
            <div
              className={cn(
                'h-full rounded-full transition-all',
                result.percentage >= 75 ? 'bg-green-500' :
                result.percentage >= 50 ? 'bg-yellow-500' : 'bg-red-500',
              )}
              style={{ width: `${result.percentage}%` }}
            />
          </div>
          <span className="text-sm font-semibold tabular-nums w-12 text-right">
            {result.percentage.toFixed(0)}%
          </span>
        </div>

        {/* Rule count */}
        <span className="text-xs text-muted-foreground w-16 text-right">
          {passedCount}/{result.rules.length} rules
        </span>

        {expanded ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
      </button>

      {expanded && (
        <div className="px-4 pb-4 border-t border-border">
          <div className="mt-3 space-y-0">
            {result.rules.map(rule => (
              <RuleRow key={rule.rule_id} rule={rule} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

interface Props {
  serviceId: string
}

export function ScorecardPanel({ serviceId }: Props) {
  const { data: results, isLoading } = useServiceScorecard(serviceId)

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2].map(i => (
          <div key={i} className="h-16 bg-muted rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  if (!results?.length) {
    return (
      <p className="text-sm text-muted-foreground py-4">
        No scorecard results available.
      </p>
    )
  }

  return (
    <div className="space-y-3">
      {results.map(result => (
        <ScoreCard key={result.template_id} result={result} />
      ))}
    </div>
  )
}
