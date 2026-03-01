import { useQuery } from '@tanstack/react-query'
import { listServices } from '@/features/catalog/api'
import { useAuthStore } from '@/features/auth/authStore'

export function useMyServices() {
  const user = useAuthStore((s) => s.user)

  return useQuery({
    queryKey: ['dashboard', 'my-services', user?.email],
    queryFn: async () => {
      const result = await listServices({ limit: 10 })
      if (!user?.email) return result.data
      // Filter by team matching user or show all if no match
      const myTeam = user.email.split('@')[0]
      const filtered = result.data.filter(
        (s) => s.team.toLowerCase().includes(myTeam) || s.team === user.name,
      )
      return filtered.length > 0 ? filtered : result.data.slice(0, 5)
    },
    enabled: !!user,
  })
}
