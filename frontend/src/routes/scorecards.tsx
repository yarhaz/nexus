import { createFileRoute } from '@tanstack/react-router'
import { ScorecardsPage } from '@/features/scorecards/ScorecardsPage'

export const Route = createFileRoute('/scorecards')({
  component: ScorecardsPage,
})
