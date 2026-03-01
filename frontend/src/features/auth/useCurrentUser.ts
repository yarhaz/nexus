import { useQuery } from '@tanstack/react-query'
import { useMsal } from '@azure/msal-react'
import { useAuthStore } from './authStore'
import { setTokenProvider } from '@/lib/api/client'
import { loginRequest } from './msalConfig'
import { apiGet } from '@/lib/api/client'
import type { CurrentUser } from '@/types/entities'

export function useCurrentUser() {
  const { instance, accounts } = useMsal()
  const { setAccount, setUser } = useAuthStore()

  const account = accounts[0] ?? null

  // Wire up the token provider once
  setTokenProvider(async () => {
    if (!account) return null
    try {
      const result = await instance.acquireTokenSilent({
        ...loginRequest,
        account,
      })
      return result.accessToken
    } catch {
      return null
    }
  })

  return useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const user = await apiGet<CurrentUser>('api/v1/auth/me')
      setUser(user)
      if (account) setAccount(account)
      return user
    },
    enabled: !!account,
    staleTime: 1000 * 60 * 10,
  })
}
