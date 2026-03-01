import { createFileRoute } from '@tanstack/react-router'
import { ActionsList } from '@/features/actions/ActionsList'

export const Route = createFileRoute('/actions')({
  component: ActionsList,
})
