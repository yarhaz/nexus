import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AccountInfo } from '@azure/msal-browser'
import type { CurrentUser } from '@/types/entities'

interface AuthState {
  account: AccountInfo | null
  user: CurrentUser | null
  isAuthenticated: boolean
  setAccount: (account: AccountInfo | null) => void
  setUser: (user: CurrentUser | null) => void
  clear: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      account: null,
      user: null,
      isAuthenticated: false,
      setAccount: (account) => set({ account, isAuthenticated: !!account }),
      setUser: (user) => set({ user }),
      clear: () => set({ account: null, user: null, isAuthenticated: false }),
    }),
    {
      name: 'nexus-auth',
      partialize: (state) => ({ account: state.account }),
    },
  ),
)
