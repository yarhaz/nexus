import { createFileRoute } from '@tanstack/react-router'
import { OpsHub } from '@/features/ops/OpsHub'

export const Route = createFileRoute('/ops')({
  component: OpsHub,
})
