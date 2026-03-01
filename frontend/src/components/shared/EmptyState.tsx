import { PackageOpen } from 'lucide-react'
import { Link } from '@tanstack/react-router'

interface Props {
  title: string
  description?: string
  action?: { label: string; href: string }
}

export function EmptyState({ title, description, action }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <PackageOpen className="w-12 h-12 text-muted-foreground/40 mb-4" />
      <h3 className="font-semibold text-foreground">{title}</h3>
      {description && <p className="text-muted-foreground text-sm mt-1 max-w-xs">{description}</p>}
      {action && (
        <Link
          to={action.href as any}
          className="mt-4 text-sm text-primary hover:underline font-medium"
        >
          {action.label}
        </Link>
      )}
    </div>
  )
}
