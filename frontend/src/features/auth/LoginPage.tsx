import { motion } from 'framer-motion'
import { useMsal } from '@azure/msal-react'
import { loginRequest } from './msalConfig'
import { Button } from '@/components/ui/button'

export function LoginPage() {
  const { instance } = useMsal()

  const handleLogin = () => {
    instance.loginRedirect(loginRequest)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-950 via-slate-900 to-slate-950">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="bg-card border border-border rounded-2xl p-10 w-full max-w-sm shadow-2xl text-center"
      >
        <div className="mb-8">
          <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl font-bold text-primary">N</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground">Nexus IDP</h1>
          <p className="text-muted-foreground text-sm mt-1">Internal Developer Platform</p>
        </div>

        <Button onClick={handleLogin} className="w-full" size="lg">
          Sign in with Microsoft
        </Button>

        <p className="text-xs text-muted-foreground mt-6">
          Use your organization account to continue
        </p>
      </motion.div>
    </div>
  )
}
